<?php require_once('functions.php') ?>
<a class="sr-only" href="#content">Skip to main content</a>
<header class="navbar navbar-static-top" id="top" role="banner">
<div class="container-fluid">
  <div class="navbar-header">
    <button class="navbar-toggle" type="button" data-toggle="collapse" data-target=".navbar-collapse">
      <span class="sr-only">Toggle Navigation</span>
      <span class="icon-bar"></span>
      <span class="icon-bar"></span>
      <span class="icon-bar"></span>
    </button>
    <a href="./" class="navbar-brand"><img src="./images/logo-videocache.png" alt="VideoCache" /></a>
  </div>
  <nav class="navbar navbar-collapse" role="navigation">
  <ul class="navbar-nav nav">
    <li class="<?php if ($current_page == 'videocache') { print 'active'; } ?>"><a href="./videocache/">VideoCache</a></li>
    <li class="<?php if ($current_page == 'squid') { print 'active'; } ?>"><a href="./squid/">Squid</a></li>
    <li class="<?php if ($current_page == 'apache') { print 'active'; } ?>"><a href="./apache/">Apache</a></li>
    <li class="<?php if ($current_page == 'cached-videos') { print 'active'; } ?>"><a href="./cached-videos/">Cache Videos</a></li>
  </ul>
  <ul class="nav navbar-right navbar-nav">
    <?php if (logged_in()) { ?>
    <li><a href="./logout">Logout</a></li>
    <? } else { ?>
    <li><a href="./login">Login</a></li>
    <?php } ?>
  </ul>
  </nav>
</div>
</header>
