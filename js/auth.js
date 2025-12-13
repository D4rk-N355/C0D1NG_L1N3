import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import {
  getAuth,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  signOut
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
import {
  getFirestore,
  doc,
  setDoc,
  getDoc
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

// ===== Firebase 初始化 =====
const firebaseConfig = {
  apiKey: "AIzaSyCEiWmpRWDVtbA2ULPNFcpJ1Wuo-z9Tjm8",
  authDomain: "coding-line-f7559.firebaseapp.com",
  projectId: "coding-line-f7559",
  storageBucket: "coding-line-f7559.firebasestorage.app",
  messagingSenderId: "61606647400",
  appId: "1:61606647400:web:147c6ebee77694c705cddd",
  measurementId: "G-M2B5FSW3SL"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);

// ===== UI 元件 =====
const feedback = document.getElementById("feedback");
const title = document.getElementById("authTitle");
const switchBtn = document.getElementById("switchBtn");
const extraField = document.getElementById("extraField");
const authForm = document.getElementById("authForm");
const logoutBtn = document.getElementById("logoutBtn");
const suPanel = document.getElementById("suPanel");

let mode = "login"; // 初始狀態：登入

function renderAuthForm() {
  if (mode === "login") {
    title.textContent = "登入";
    switchBtn.textContent = "切換到註冊";
    extraField.innerHTML = ""; // 登入不需要暱稱
  } else {
    title.textContent = "註冊";
    switchBtn.textContent = "切換到登入";
    extraField.innerHTML = `<input type="text" id="nickname" placeholder="暱稱" required><br>`;
  }
}

switchBtn.addEventListener("click", () => {
  mode = mode === "login" ? "register" : "login";
  renderAuthForm();
});

authForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();

  try {
    if (mode === "login") {
      await signInWithEmailAndPassword(auth, email, password);
      feedback.textContent = "登入成功，跳轉到留言板";
      window.location.href = "post.html";
    } else {
      const nickname = document.getElementById("nickname").value.trim();
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const uid = userCredential.user.uid;

      // 寫入 Firestore
      await setDoc(doc(db, "users", uid), {
        nickname,
        role: "member", // 預設角色
        email,
        createAt: new Date()
      });

      // 驗證是否成功寫入
      const verifyDoc = await getDoc(doc(db, "users", uid));
      if (verifyDoc.exists() && verifyDoc.data().nickname === nickname) {
        feedback.textContent = "註冊成功，請重新登入";
        feedback.style.color = "green";

        // 立即登出，避免自動登入
        await signOut(auth);
        window.location.href = "index.html";
      } else {
        feedback.textContent = "註冊成功，但暱稱儲存失敗";
        feedback.style.color = "red";
      }
    }
  } catch (err) {
    feedback.textContent = (mode === "login" ? "登入失敗：" : "註冊失敗：") + err.message;
    feedback.style.color = "red";
  }
});

// 初始渲染
renderAuthForm();

// ===== 登入狀態監聽 =====
onAuthStateChanged(auth, async (user) => {
  if (user) {
    logoutBtn.style.display = "inline-block"; // 顯示登出按鈕
    const userDoc = await getDoc(doc(db, "users", user.uid));
    if (userDoc.exists()) {
      const role = userDoc.data().role;
      console.log("登入中，角色:", role);

      if (role === "su") {
        suPanel.style.display = "block"; // 顯示 SU 專屬功能
      }
    }
  } else {
    logoutBtn.style.display = "none";
    suPanel.style.display = "none";
    console.log("尚未登入");
  }
});

// ===== 登出功能 =====
logoutBtn.addEventListener("click", async () => {
  try {
    await signOut(auth);
    window.location.href = "index.html";
  } catch (err) {
    console.error("登出失敗:", err);
  }
});