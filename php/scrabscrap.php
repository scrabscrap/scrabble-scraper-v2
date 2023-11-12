<?php
  // an example to accept post request for http(s) transfer of game information
  //
  // for security reasons use this script only in protected areas of the web server
  // default folder structure:
  //    <scrabscrap folder on web server>
  //        /bin/scrabscrap.php
  //        /web/
  // ./bin/ Folder is protected by .htaccess
  
  // configure correct path for your web server - (in this example ./bin/../web/)
  $path = getcwd()."/../web/";

if(isset($_POST["delete"])) {

  array_map('unlink', glob($path."image-*.png"));
  array_map('unlink', glob($path."image-*.jpg"));
  array_map('unlink', glob($path."data-*.json"));

} elseif (isset($_POST["upload"])) {

  $errors = []; // Store errors here
  $noerrors = [];
  $fileExtensionsAllowed = ['jpeg','jpg','png', 'json', 'zip']; // These will be the only file extensions allowed 

  foreach($_FILES as $file) {
      $fileName = $file['name'];
      $fileSize = $file['size'];
      $fileTmpName  = $file['tmp_name'];
      $fileType = $file['type'];
      $fileExtension = strtolower(end(explode('.',$fileName)));

      $uploadPath = $path . basename($fileName); 
      if (! in_array($fileExtension,$fileExtensionsAllowed)) {
          $errors[] = "ERROR: " . basename($fileName) . " NOK - invalid file extension\n";
      }
  
      // if (($fileExtension != 'zip') && ($fileSize > 4000000)) {
      //    $errors[] = "ERROR: " . basename($fileName) . " NOK - Filesize\n";
      // }
      if (empty($errors)) {
          $didUpload = move_uploaded_file($fileTmpName, $uploadPath);
          if ($didUpload) {
            $noerrors[] = "" . basename($fileName) . "\n";
          } else {
            http_response_code(400);
            echo "ERROR: " . basename($fileName) . " NOK\n";
            exit;
          }
      } else {
          http_response_code(400);
          foreach ($errors as $error) {
            echo $error;
          }
          exit;
      }
  }
  foreach ($noerrors as $msg) {
    echo $msg;
  }

} else {
  http_response_code(400);
  echo "ERROR: invalid operation";
  exit;
}

?>