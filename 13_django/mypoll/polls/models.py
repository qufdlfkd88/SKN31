from django.db import models

# 모델 클래스들을 정의 - Question(설문 질문), Choice(설문 보기)
## - Model을 상속
## - class이름: 단수형
## - class변수로 Field들을 정의. (Field - Table의 컬럼)
### - Field: 필드이름(컬럼이름, instance변수 이름) = Field객체(컬럼 설정)
### - primary key Field가 없으면 자동으로 생성
### - Field명 : id, type: 양의정수, 1씩 자동 증가
### - 특정 Field를 PK로 설정하려면 Field(primary_key=True) 로 설정

# Question Model Class 정의
class Question(models.Model):                                 # create table question
    # 질문문장
    question_text = models.CharField(max_length=200)          #   question_text, varchar(200)
    # 질문등록일시
    pub_date = models.DateTimeField(auto_now_add=True)        #   pub_date datetime
    # auto_now_add=True : insert 시점의 일시를 자동으로 입력

