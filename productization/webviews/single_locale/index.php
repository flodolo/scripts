<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset=utf-8>
    <title>Searchplugins</title>
    <style type="text/css">
    body {
        background-color: #CCC;
        font-family: Arial, Verdana;
        font-size: 14px;
    }

    p {
        margin-top: 2px;
    }

    div#localelist {
        background-color: #FAFAFA;
        padding: 6px;
        border: 1px solid #555;
        border-radius: 8px;
        line-height: 1.7em;
        font-size: 16px;
        width: 800px;
        margin-bottom: 20px;
    }

    div.searchplugin {
        background-color: #FAFAFA;
        min-height: 130px;
        margin-top: 6px;
        border: 1px solid #555;
        border-radius: 8px;
    }

    div.searchplugin img {
        display: block;
        margin: 5px auto;
    }

    div.image {
        display: block;
        text-align: center;
        width: 100%;
        float: left;
        padding: 3px;
    }

    div.info {
        padding: 3px;
    }

    div.searchplugin p {
        margin: 2px 6px;
    }

    div.product h2 {
        clear: both;
        padding-top: 36px;
        text-transform: uppercase;
    }

    div.channel {
        width: 280px;
        float: left;
        padding: 0 3px;
    }

    div.channel h3 {
        text-transform: uppercase;
        text-align: center;
    }

    p.error {
        color: red;
    }

    p.http {
        color: #F28D49;
    }

    p.https {
        color: #35B01C;
    }

    div.searchplugin p.emptysp {
        margin-top: 24px;
    }
    </style>
</head>

<body>

<?php

    include_once('../locales.inc');
    $jsondata = file_get_contents("../searchplugins.json");
    $jsonarray = json_decode($jsondata, true);

    $channels = array('trunk', 'aurora', 'beta', 'release');
    $products = array('browser', 'metro', 'mobile', 'suite', 'mail');
    $productnames = array('Firefox Desktop', 'Firefox Metro', 'Firefox Mobile (Android)', 'Seamonkey', 'Thunderbird');

    # Single locale
    $locale = !empty($_REQUEST['locale']) ? $_REQUEST['locale'] : 'en-US';

    echo "  <h1>Current locale: $locale</h1>\n";
    echo "  <div id='localelist'>
    <p>Available locales <br/>\n";
    foreach ($locales as $localecode) {
        echo '      <a href="?locale=' . $localecode . '">' . $localecode . "</a> \n";
    }
    echo "    </p>
  </div>\n\n";

    echo '  <p id="update">Last update: ' . $jsonarray["creation_date"] . "</p>\n";

    foreach ($products as $i=>$product) {
        echo "  <div class='product'>
    <h2><a href='#" . $productnames[$i] ."' id='" . $productnames[$i] ."' >" . $productnames[$i] ."</a></h2>\n";
        if (array_key_exists($product, $jsonarray[$locale])) {
            # This product exists in locale
            foreach ($channels as $channel) {
                echo "      <div class='channel'>
        <h3>$channel</h3>\n";
                if (array_key_exists($channel, $jsonarray[$locale][$product])) {
                    foreach ($jsonarray[$locale][$product][$channel] as $key => $singlesp) {
                        if ($key != 'p12n') {
                            echo '        <div class="searchplugin">' . "\n";
                            echo '          <div class="image">' . "\n";
                            foreach ($singlesp['images'] as $imageindex) {
                                echo '            <img src="' . $jsonarray['images'][$imageindex] . '" alt="searchplugin icon" />' . "\n";
                            }
                            echo "          </div>\n";

                            echo '          <div class="info">' . "\n";
                            if ( $singlesp['name'] == 'not available') {
                                echo '            <p class="error"><strong>' . $singlesp['name'] . '</strong> (' . $singlesp['file'] . ')</p>' . "\n";
                            } else {
                                echo '            <p><strong>' . $singlesp['name'] . '</strong> (' . $singlesp['file'] . ')</p>' . "\n";
                            }

                            if ( strpos($singlesp['description'], 'not available')) {
                                echo '            <p class="error">' . $singlesp['description'] . '</p>' . "\n";
                            } else {
                                echo '            <p>' . $singlesp['description'] . '</p>' . "\n";
                            }

                            echo '            <p>Locale: ' . $locale . '</p>' . "\n";

                            if ($singlesp['secure']) {
                                echo '            <p class="https" title="Connection over https">URL: <a href="' . $singlesp['url'] . '">link</a></p>' . "\n";
                            } else {
                                echo '            <p class="http" title="Connection over http">URL: <a href="' . $singlesp['url'] . '">link</a></p>' . "\n";
                            }
                            echo "          </div>
        </div>\n";                        }
                    }
                } else {
                    # Product exists, but not on this channel
                    echo "      <div class='searchplugin'>
        <p class='emptysp'>No plugin available for the selected locale on this channel.</p>
      </div>\n";
                }
                echo "      </div>\n";
            }
        } else {
            echo "    <p>This product is not available for this locale.</p>\n";
        }
        echo "  </div>\n";
    }
