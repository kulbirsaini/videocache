<?php
  session_start();
  if ($_SESSION['login'] == true || ($_POST['username'] == 'admin' && $_POST['password'] == 'password')) {
    $_SESSION['login'] = true;
    if ($current_page == 'login') {
      header('Location: ' . ROOT_PATH);
    }
  } elseif ($current_page != 'login') {
    header('Location: ' . ROOT_PATH . '/login');
  }
?>
