import { auth, db } from "./firebase.js";
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
import { doc, getDoc } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

onAuthStateChanged(auth, async (user) => {
  if (!user) {
    window.location.href = "index.html";
    return;
  }

  const userDoc = await getDoc(doc(db, "users", user.uid));
  const role = userDoc.exists() ? userDoc.data().role : "member";

  if (role !== "su") {
    alert("你沒有權限訪問此頁面");
    window.location.href = "index.html";
    return;
  }

  document.getElementById("suPanel").textContent = "歡迎 SU 使用者！載入管理功能中...";
});