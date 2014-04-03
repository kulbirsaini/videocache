<?php $current_page = 'login' ?>
<?php include('./shared/functions.php'); ?>
<?php include('./shared/require-login.php'); ?>
<!Doctype html>
<html lang="en" class="stretch-height">
  <?php include('./shared/head.php') ?>
  <body class="stretch-height no-margin no-padding">
    <style type="text/css">
      #content { margin: 0; padding: 0; }
      .wrapper { width: 100%; }
    </style>
    <div id="content" class="text-center stretch-height">
      <div class="container-fluid stretch-height vcenter">
        <div class="wrapper">
          <div class="row">
            <h1>VideoCache Web Frontend</h1>
            <p>Manage your VideoCache server via a responsive web interface.</p>
          </div>
          <div class="row login-box">
            <div class="col-xs-8 col-sm-4 col-md-2 well well-lg centered">
              <form action="<?php print ROOT_PATH ?>/login" method="POST" role="form" class="form-horizontal">
                <div class="form-group">
                  <div class="col-sm-12 col-xs-12 col-md-12">
                    <input type="text" class="form-control" id="username" name="username" placeholder="Username">
                  </div>
                </div>
                <div class="form-group">
                  <div class="col-sm-12 col-xs-12 col-md-12">
                    <input type="password" class="form-control" name="password" id="password" placeholder="Password">
                  </div>
                </div>
                <div class="form-group text-left">
                  <div class="col-sm-12 col-xs-12 col-md-12">
                    <button type="submit" id="login" class="btn btn-default">Login</button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>
