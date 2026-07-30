from django import forms

# ModelForm: form.ModelForm을 상속해서 구현
#            Meta Class (Inner Class로 정의)에서 어떤 Model을 이용해서 만들지 그 Model의 어떤 Field들을 입력폼으로 사용할지 설정.
#            Model에 없는 것을 입력 Field로 등록할 경우 class변수로 설정하면됨.(Form과 동일)

# Django에서 사용자 관리(등록, 수정)을 위해서 제공하는 ModelForm들.
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import CustomUser

# 등록 화면에서 사용할 Form
class CustomUserCreationForm(UserCreationForm):

    # UserCreateForm의 Field를 재정의 하는 경우
    username = forms.CharField(label="ID", required=True, max_length=30)

    # UserCreateForm에 없는 Field 등록
    # age = forms.IntegerField(label="나이")

    class Meta:
        model = CustomUser  # 연결할 Model을 지정
        fields = ["username", "password1", "password2", "name", "email", "birthday"]
        # 입력양식에 추가할 Model의 Field들을 정의
        # [Field 선택, ...]: form을 만드는데 사용할 필드들을 선택
        # fields = "__all__" : 모든 필드들을 이용해서 form을 구성
        ## exclude = ['필드명'] 지정한 field들 빼고 나머지 field들을 이용.

        # 특정 Field들의 Widget을 변경
        widgets = {
            "birthday":forms.DateInput(attrs={"type":"date"})   # DateInput: 날짜 형식입력. type=date 정의
        }

    # 검증 메소드 추가
    def clean_name(self):
        name = self.cleaned_data['name']
        if len(name) < 2:
            raise forms.ValidationError("이름은 두 글자 이상 입력하세요.")

        return name


############ 사용자 정보 변경 폼 ################
class CustomUserChangeForm(UserCreationForm):
    password = None

    class Meta:
        model = CustomUser
        fields = ["name", "email", "birthday"]
        widgets = {
            "birthday": forms.DateInput(attrs={"type":"date"})
        }

    # 검증 메소드 추가
    def clean_name(self):
        name = self.cleaned_data['name']
        if len(name) < 2:
            raise forms.ValidationError("이름은 두 글자 이상 입력하세요.")

        return name
