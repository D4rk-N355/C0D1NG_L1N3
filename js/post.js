import { auth, db } from "./firebase.js";
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
import { doc, getDoc } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

const API_URL = "https://script.google.com/macros/s/AKfycbx6UdvQqj0NABc2ngtTkyzk5dU9CwaMXOIbjUWmMab65A9HqoD387pXY49wHOpBsL-GEg/exec";

const postForm = document.getElementById("postForm");
const postContent = document.getElementById("postContent");
const feedback = document.getElementById("feedback");
const userDisplay = document.getElementById("currentUser");

let currentNickname = null;
import { signOut } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

document.getElementById("logoutBtn").addEventListener("click", async () => {
  try {
    await signOut(auth);
    window.location.href = "index.html";
  } catch (err) {
    console.error("登出失敗:", err);
  }
});
// ===== 登入狀態監聽 =====
onAuthStateChanged(auth, async (user) => {
  if (user) {
    try {
      const userDoc = await getDoc(doc(db, "users", user.uid));
      if (userDoc.exists() && userDoc.data().nickname) {
        currentNickname = userDoc.data().nickname;
        userDisplay.textContent = `目前暱稱：${currentNickname}`;
      } else {
        currentNickname = null;
        userDisplay.textContent = "目前暱稱：未設定";
        feedback.textContent = "暱稱錯誤，請重新登入或註冊";
        feedback.style.color = "red";
      }
    } catch (err) {
      currentNickname = null;
      userDisplay.textContent = "目前暱稱：錯誤";
      feedback.textContent = "暱稱讀取失敗：" + err.message;
      feedback.style.color = "red";
    }
  } else {
    window.location.href = "login.html";
  }
});

// ===== 發文事件 =====
postForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  if (!currentNickname) {
    feedback.textContent = "暱稱錯誤，無法發文";
    feedback.style.color = "red";
    return;
  }

  const content = postContent.value.trim();
  if (!content) {
    feedback.textContent = "請輸入內容！";
    feedback.style.color = "red";
    return;
  }

  feedback.textContent = "傳送中...";
  feedback.style.color = "blue";

  try {
    const formData = new URLSearchParams();
    formData.append("nickname", currentNickname);
    formData.append("content", content);

    const res = await fetch(API_URL, {
      method: "POST",
      body: formData
    });

    const resultText = await res.text();

    if (resultText.trim() === "ok") {
      feedback.textContent = "送出成功！";
      feedback.style.color = "green";
      postContent.value = "";
    } else {
      feedback.textContent = "送出失敗：" + resultText;
      feedback.style.color = "red";
    }
  } catch (err) {
    feedback.textContent = "送出失敗：" + err.message;
    feedback.style.color = "red";
    console.error(err);
  }
});