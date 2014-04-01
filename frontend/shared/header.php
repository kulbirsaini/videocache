<?php require_once('functions.php'); ?>
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
    <a href="<?php print ROOT_PATH; ?>" class="navbar-brand" title="WHITE MAGNET">WHITE MAGNET</a>
  </div>
  <nav class="navbar navbar-collapse" role="navigation">
  <ul class="navbar-nav nav">
    <li class="<?php if ($current_page == 'home') { print 'active'; } ?>"><a href="<?php print ROOT_PATH; ?>">Home</a></li>
    <li class="<?php if ($current_page == 'videocache') { print 'active'; } ?>"><a href="<?php print ROOT_PATH; ?>/videocache">VideoCache</a></li>
    <li class="<?php if ($current_page == 'squid') { print 'active'; } ?>"><a href="<?php print ROOT_PATH; ?>/squid">Squid</a></li>
    <li class="<?php if ($current_page == 'apache') { print 'active'; } ?>"><a href="<?php print ROOT_PATH; ?>/apache">Apache</a></li>
    <li class="<?php if ($current_page == 'browse') { print 'active'; } ?>"><a href="<?php print ROOT_PATH; ?>/browse">Browse</a></li>
  </ul>
  <ul class="nav navbar-right navbar-nav">
    <?php if (logged_in()) { ?>
    <li><a href="<?php print ROOT_PATH; ?>/logout">Logout</a></li>
    <? } else { ?>
    <li><a href="<?php print ROOT_PATH; ?>/login">Login</a></li>
    <?php } ?>
  </ul>
  </nav>
</div>
</header>
