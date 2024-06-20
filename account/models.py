from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date, datetime, time

class User(AbstractUser):
    ROLE_CHOICES = [
        ('Manager', 'Manager'),
        ('Boshqaruvchi', 'Boshqaruvchi'),
        ('Ustoz', 'Ustoz'),
        ('Oquvchi', 'Oquvchi')
    ]
    status = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Oquvchi')
    photo = models.ImageField(upload_to='user/', default='1.png')
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    
    # USERNAME_FIELD = 'username'
    # REQUIRED_FIELDS = []

    def __str__(self):
        return self.username
    

class Subject(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class TeacherSubject(models.Model):
    teacher = models.ForeignKey(User, limit_choices_to={'status': 'Ustoz'}, on_delete=models.CASCADE, related_name='teacher_subject')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='teacher_subject')

    def __str__(self):
        return f"{self.teacher.username} - {self.subject.name}"

class PreEnrollment(models.Model):
    student = models.ForeignKey(User, limit_choices_to={'status': 'Oquvchi'}, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='new_pupils')
    registration_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.subject.name}"

class Room(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

class Group(models.Model):
    name = models.CharField(max_length=100)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='groups')
    teacher = models.ForeignKey(User, limit_choices_to={'status': 'Ustoz'}, on_delete=models.CASCADE, related_name='teacher_groups')
    students = models.ManyToManyField(User, through='Enrollment', limit_choices_to={'status': 'Oquvchi'}, related_name='student_groups')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='room_groups')
    days = models.CharField(max_length=100, null=True, blank=True)  # e.g. "Monday, Wednesday, Friday"
    start_time = models.TimeField()  # e.g. "10:00"
    end_time = models.TimeField()  # e.g. "12:00"

    def __str__(self):
        return self.name

class Payment(models.Model):
    student = models.ForeignKey(User, limit_choices_to={'status': 'Oquvchi'}, on_delete=models.CASCADE, related_name='student_payments')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.student.username} - {self.group.name} - {self.amount}"

    @property
    def teacher_share(self):
        return self.amount * 0.40

class Enrollment(models.Model):
    student = models.ForeignKey(User, limit_choices_to={'status': 'Oquvchi'}, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_enrolls')
    enrollment_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.group.name}"

class Attendance(models.Model):
    student = models.ForeignKey(User, limit_choices_to={'status': 'Oquvchi'}, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    date = models.DateField()
    present = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} - {self.group.name} - {self.date} - {'Present' if self.present else 'Absent'}"

class Schedule(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    day = models.CharField(max_length=10, choices=[
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.group.name} - {self.day} - {self.start_time}-{self.end_time}"

def create_group(name, subject, teacher, room, days, start_time, end_time):
    # Check if the teacher is eligible to teach the subject
    if not TeacherSubject.objects.filter(teacher=teacher, subject=subject).exists():
        raise ValueError("This teacher is not eligible to teach this subject.")

    group = Group.objects.create(
        name=name,
        subject=subject,
        teacher=teacher,
        room=room,
        days=days,
        start_time=start_time,
        end_time=end_time
    )
    
    # Create schedule entries
    for day in days.split(','):
        Schedule.objects.create(group=group, day=day.strip(), start_time=start_time, end_time=end_time)
    
    # PreEnrollment'dan talabalarni guruhga o'tkazish
    pre_enrollments = PreEnrollment.objects.filter(subject=subject)
    for pre_enrollment in pre_enrollments:
        Enrollment.objects.create(student=pre_enrollment.student, group=group)
        pre_enrollment.delete()
    
    return group

def calculate_debt(student, group):
    current_year = date.today().year
    current_month = date.today().month

    enrollment = Enrollment.objects.get(student=student, group=group)
    subject = group.subject
    monthly_fee = subject.monthly_fee

    # Total months since enrollment
    total_months = (current_year - enrollment.enrollment_date.year) * 12 + current_month - enrollment.enrollment_date.month + 1

    # Total amount due
    total_due = total_months * monthly_fee

    # Total amount paid
    total_paid = Payment.objects.filter(student=student, group=group).aggregate(models.Sum('amount'))['amount__sum'] or 0

    # Debt calculation
    debt = total_due - total_paid

    return debt
