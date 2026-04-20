# app.py
from src.common import utils
print("app 테스트")
utils.util_func()

# 실행
# project root directory 아래서 실행
# python src\test\app.py -> app.py 실행: root dir 실행시킨 app.py가 있는 디렉토리

# python -m src.test.app *(-m을 하면 루트로 감)*
# 실행하는 디렉토리가 root directory가 되서 import의 시작이됨
# -m은 모듈로 실행시키는 것.