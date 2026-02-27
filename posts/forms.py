from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import FamilyMemberPhoto, FamilyPost


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(file_item, initial) for file_item in data]
        return single_file_clean(data, initial)


class FamilyLoginForm(AuthenticationForm):
    username = forms.CharField(label='아이디', max_length=150)
    password = forms.CharField(label='비밀번호', widget=forms.PasswordInput)


class FamilyMemberPhotoForm(forms.ModelForm):
    images = MultipleFileField(
        label='사진',
        required=False,
        help_text='여러 장 선택 후, 아래 미리보기에서 대표사진 체크박스를 선택하세요. 사진은 파일당 최대 200MB까지 업로드 가능합니다.',
    )
    captured_at = forms.DateTimeField(
        label='촬영/작성 날짜와 시간',
        required=False,
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text='비워두면 현재 시간이 저장됩니다.',
    )
    event_date = forms.DateField(
        label='이벤트 날짜',
        required=False,
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='과거 사진이라면 실제 행사/이벤트 날짜를 선택하세요.',
    )
    videos = MultipleFileField(
        label='동영상',
        required=False,
        widget=MultipleFileInput(attrs={'accept': 'video/*'}),
        help_text='동영상은 파일당 최대 200MB까지 업로드 가능하며, 업로드 시 200MB 이하로 압축 저장됩니다.',
    )
    tags = forms.CharField(
        label='태그',
        required=False,
        help_text='쉼표 또는 #태그 형식으로 입력하세요. 예: 여행, 바다 또는 #여행 #바다',
    )

    caption = forms.CharField(label='설명', required=False, max_length=120)

    class Meta:
        model = FamilyMemberPhoto
        fields = ['images', 'caption']


class FamilyMemberCreateForm(UserCreationForm):
    EMOJI_CHOICES = [
        ('🙂', '🙂 미소'),
        ('😀', '😀 웃음'),
        ('😄', '😄 활짝'),
        ('🥰', '🥰 하트'),
        ('😎', '😎 멋짐'),
        ('🤗', '🤗 포옹'),
        ('👨', '👨 아빠'),
        ('👩', '👩 엄마'),
        ('👧', '👧 딸'),
        ('👦', '👦 아들'),
        ('👵', '👵 할머니'),
        ('👴', '👴 할아버지'),
    ]

    first_name = forms.CharField(label='이름', max_length=150, required=False)
    email = forms.EmailField(label='이메일', required=False)
    emoji = forms.ChoiceField(
        label='이모티콘',
        choices=EMOJI_CHOICES,
        required=False,
        initial='🙂',
        widget=forms.RadioSelect,
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email', 'password1', 'password2']


class FamilyPostEditForm(forms.ModelForm):
    images = MultipleFileField(
        label='사진',
        required=False,
        help_text='여러 장 선택 가능합니다. 대표사진 체크박스를 선택해 대표를 지정하세요. 사진은 파일당 최대 200MB까지 업로드 가능합니다.',
    )
    tags = forms.CharField(
        label='태그',
        required=False,
        help_text='쉼표 또는 #태그 형식으로 입력하세요. 예: 가족, 산책 또는 #가족 #산책',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tags'].initial = ', '.join(self.instance.tags.values_list('name', flat=True))

    class Meta:
        model = FamilyPost
        fields = ['title', 'content', 'event_date', 'main_image']
        labels = {
            'title': '기사 제목',
            'content': '본문 내용',
            'event_date': '이벤트 날짜',
            'main_image': '대표 사진',
        }
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date'}),
        }