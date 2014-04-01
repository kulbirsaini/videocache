<?php

include('constants.php');

function logout() {
  session_start();
  $_SESSION['login'] = false;
}

function redirect($page = null) {
  if ($page == null) { $page = ROOT_PATH; }
  header("Location: " . $page);
}

function logout_and_redirect($page = null) {
  if ($page == null) { $page = ROOT_PATH; }
  logout();
  redirect($page);
}

function logged_in() {
  return $_SESSION['login'] == true;
}

?>
