<?php $current_page = 'login' ?>
<?php include('./shared/prefix-html.php') ?>
<div id="content" class="text-center">
  <div class="container-fluid">
    <h1>VideoCache Web Frontend</h1>
    <p>Manage your VideoCache server via a responsive web interface.</p>
    <div class="row login-box">
      <div class="col-xs-12 col-sm-4 col-sm-offset-4 col-md-2 col-md-offset-5 well well-lg">
        <form action="./login" method="POST" role="form" class="form-horizontal">
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
          <div class="form-group">
            <div class="col-sm-12 col-xs-12 col-md-12">
              <button type="submit" id="login" class="btn btn-default">Login</button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</div>
<?php include('./shared/suffix-html.php') ?>
