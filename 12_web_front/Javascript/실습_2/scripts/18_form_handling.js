const signupForm = document.querySelector("#signup-form");
const validationMessage = document.querySelector("#validation-message");
const submitResult = document.querySelector("#submit-result");

// 결과 목록에 한 줄을 추가한다.
function appendResultLine(text) {
  const item = document.createElement("li"); //<li></li> 생성

  item.textContent = text; // <li>text</li>
  submitResult.append(item); // 자식노드로 추가
}

// 18.6 입력값 검증: 이름이 비어 있으면 false를 반환하고 포커스를 이동한다.
function validateName() {
  const name = signupForm.elements.name.value.trim();

  // if (!name) {
  if (name.length < 3) { // 이름이 3글자 이상
    validationMessage.textContent = "이름을 입력하세요."; // "세글자이상 입력하세요"
    signupForm.elements.name.focus(); // 이름 칸으로 포커스를 옮김
    return false;
  }

  validationMessage.textContent = "입력값이 올바릅니다.";
  return true;
}

// 18.1 폼 제출 + 18.2 FormData + 18.4 체크박스 + 18.5 라디오 버튼
function handleSignupSubmit(event) {
  event.preventDefault(); // 기본 전송(새로고침)을 막는다.
  // validation check를 하지 않고 submit 이 되어 버림
  submitResult.innerHTML = "";
  
  // 입력 값 검증 (name)
  if (!validateName()) {
    return;
  }

  // (검증 통과하면)서버로 전송
  // signupForm.submit();  // form객체.submit() 전송, .reset() 입력값들 초기화

  const formData = new FormData(signupForm);

  // get(): 해당 이름의 첫 번째 값을 반환한다. 값이 없으면 null.
  const name = formData.get("name");  // name 입력의 value 값 조회
  const age = formData.get("age");    // age 입력의 value 값 조회
  appendResultLine(`이름: ${name}`);
  appendResultLine(`나이: ${age} (숫자로 변환: ${Number(age)})`);

  // 18.4 체크박스: 선택 여부는 checked로 확인한다. true, false 로 확인
  const agreeChecked = signupForm.elements.agree.checked;
  const agreeValue = formData.get("agree");

  appendResultLine(`약관 동의 여부(checked): ${agreeChecked}`);
  appendResultLine(`약관 동의 값(value): ${agreeValue}`);

  // getAll(): 같은 이름을 가진 모든 값을 배열로 반환한다.
  const hobbies = formData.getAll("hobby");
  appendResultLine(`선택한 취미(getAll): ${hobbies.length > 0 ? hobbies.join(", ") : "(없음)"}`);

  // 18.5 라디오 버튼: 선택된 항목의 value를 반환한다. 없으면 null.
  const level = formData.get("level");
  appendResultLine(`선택한 수준: ${level === null ? "(선택 안 함)" : level}`);

  // entries()를 일반 객체로 변환해 전체 데이터를 콘솔에서 확인한다.
  const data = Object.fromEntries(formData.entries());
  console.log("폼 전체 데이터(Object.fromEntries):", data);
}

// 18.3 폼 요소 접근 (form.elements)
const readElementsButton = document.querySelector("#read-elements-button");
const elementsResult = document.querySelector("#elements-result");

function readFormElements() {
  const nameInput = signupForm.elements.name;
  const agreeInput = signupForm.elements.agree;

  elementsResult.textContent =
    `이름 입력값: "${nameInput.value}" / 약관 동의: ${agreeInput.checked}`;
  console.log("form.elements.name.value:", nameInput.value);
  console.log("form.elements.agree.checked:", agreeInput.checked);
}

// 이벤트 등록
signupForm.addEventListener("submit", handleSignupSubmit);
readElementsButton.addEventListener("click", readFormElements);
