<?php

function logout() {
  session_start();
  $_SESSION['login'] = false;
}

function redirect($page = "./") {
  header("Location: " . $page);
}

function logout_and_redirect($page = "./") {
  logout();
  redirect($page);
}

function logged_in() {
  return $_SESSION['login'] == true;
}

?>
