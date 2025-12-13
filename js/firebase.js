// js/firebase.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

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