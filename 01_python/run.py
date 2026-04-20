#calc 모듈의 함수들을 호출 하려면 calc모듈을 import 해야한다.
#import calc
import calc as c
result = c.plus(20, 30) # 같은 모듈에 정의된 함수 호출
print(result)
print(c.minus(100,20))