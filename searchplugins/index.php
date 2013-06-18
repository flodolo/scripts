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
    }

    div.searchplugin {
        background-color: #FAFAFA;
        padding: 12px 6px;
        min-height: 100px;
        margin-top: 6px;
        border: 1px solid #555;
        border-radius: 8px;
    }

    div.searchplugin img {
        float: left;
        margin-right: 4px;
    }

    div.searchplugin p {
        margin-left: 30px;
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
    </style>
</head>

<body>

<?php

    function preg_array_key_exists($pattern, $array) {
        $keys = array_keys ($array);
        return preg_grep ($pattern, $keys);
    }

    $jsondata = file_get_contents("searchplugins.json");
    $jsonarray = json_decode($jsondata, true);

    $channels = array('release', 'beta', 'aurora', 'trunk');
    $products = array('browser', 'mobile', 'mail', 'suite');
    $productnames = array('Firefox', 'Firefox for Android', 'Thunderbird', 'SeaMonkey');

    $locales = array('ach', 'af', 'ak', 'an', 'ar', 'as', 'ast', 'be', 'bg', 'bn-BD',
        'bn-IN', 'br', 'bs', 'ca', 'cs', 'csb', 'cy', 'da', 'de', 'el',
        'en-GB', 'en-ZA', 'eo', 'es-AR', 'es-CL', 'es-ES', 'es-MX', 'et', 'eu', 'fa',
        'ff', 'fi', 'fr', 'fy-NL', 'ga-IE', 'gd', 'gl', 'gu-IN', 'he', 'hi-IN',
        'hr', 'hu', 'hy-AM', 'id', 'is', 'it', 'ja', 'ja-JP-mac', 'ka', 'kk',
        'km', 'kn', 'ko', 'ku', 'lg', 'lij', 'lt', 'lv', 'mai', 'mk', 'ml', 'mr',
        'ms', 'my', 'nb-NO', 'ne-NP', 'nl', 'nn-NO', 'nr', 'nso', 'oc', 'or',
        'pa-IN', 'pl', 'pt-BR', 'pt-PT', 'rm', 'ro', 'ru', 'rw', 'si', 'sk',
        'sl', 'son', 'sq', 'sr', 'ss', 'st', 'sv-SE', 'sw', 'ta', 'ta-LK', 'te',
        'th', 'tn', 'tr', 'ts', 'uk', 've', 'vi', 'wo', 'xh', 'zh-CN', 'zh-TW',
        'zu');

    # Single locale
    $locale = !empty($_REQUEST['locale']) ? $_REQUEST['locale'] : 'en-US';

    echo "<h1>Current locale: $locale</h1>\n";
    echo "<div id='localelist'>
            <p>Available locales <br/>";
    foreach ($locales as $localecode) {
        echo '<a href="?locale=' . $localecode . '">' . $localecode . '</a>&nbsp; ';
    }
    echo "  </p>
          </div>";

    foreach ($products as $i=>$product) {
        echo "<div class='product'>
                <h2>" . $productnames[$i] ."</h2>\n";
        foreach ($channels as $channel) {
            echo "<div class='channel'>
                    <h3>$channel</h3>
                 ";
            $re = '/^' . $locale . '_' . $product . '_' . $channel . '/';
            $keys = preg_array_key_exists($re, $jsonarray);
            $printeditems = 0;
            foreach ($keys as $key) {
                echo '<div class="searchplugin">';
                echo '<img src="' . $jsonarray[$key]['image'] . '" alt="searchplugin icon" />';

                if ( $jsonarray[$key]['name'] == 'not available') {
                    echo '<p class="error"><strong>' . $jsonarray[$key]['name'] . '</strong> (' . $jsonarray[$key]['file'] . ')</p>';
                } else {
                    echo '<p><strong>' . $jsonarray[$key]['name'] . '</strong> (' . $jsonarray[$key]['file'] . ')</p>';
                }

                if ( strpos($jsonarray[$key]['description'], 'not available')) {
                    echo '<p class="error">' . $jsonarray[$key]['description'] . '</p>';
                } else {
                    echo '<p>' . $jsonarray[$key]['description'] . '</p>';
                }

                echo '<p>Locale: ' . $jsonarray[$key]['locale'] . '</p>';

                if ($jsonarray[$key]['secure']) {
                    echo '<p class="https" title="Connection over https">URL: <a href="' . $jsonarray[$key]['url'] . '">link</a></p>';
                } else {
                    echo '<p class="http" title="Connection over http">URL: <a href="' . $jsonarray[$key]['url'] . '">link</a></p>';
                }
                echo '</div>';
                $printeditems++;
            }
            if ($printeditems == 0) {
                echo "<div class='searchplugin'>
                        <p>No plugin available for the selected locale on this channel.</p>
                      </div>\n";
            }
            echo "</div>\n";
        }
        echo "</div>\n";
    }


