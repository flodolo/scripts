<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset=utf-8>
    <title>Searchplugins</title>
    <style type="text/css">
        body { background-color: #FCFCFC; font-family: Arial, Verdana; font-size: 14px; padding: 10px;}
        p { margin-top: 2px;}
        table {padding: 0; margin: 20px 0; border-collapse: collapse; color: #333; background: #F3F5F7; margin-top: 20px;}
        table a {color: #3A4856; text-decoration: none; border-bottom: 1px solid #DDD;}
        table a:visited {color: #777;}
        table a:hover {color: #000;}
        table thead th {background: #EAECEE; padding: 15px 10px; color: #000; text-align: center; font-weight: bold; vertical-align: top;}
        table tr th {background: #EAECEE;}
        table td.firstsection {padding-left: 40px; border-left: 1px solid #DDD;}
        table td.lastsection {padding-right: 40px; border-right: 1px solid #DDD;}
        table .lastsection:last-child {border-right: 0};
        table tbody, table thead {border-left: 1px solid #DDD; border-right: 1px solid #DDD;}
        table tbody {border-bottom: 1px solid #DDD;}
        table tbody td, table tbody th {padding: 5px 20px; text-align: left;}
        table tbody td {border-bottom: 1px solid #DDD}
        table tbody tr {background: #F5F5F5;}
        table tbody tr.odd {background: #F0F2F4;}
        table tbody tr:hover {background: #EAECEE; color: #111;}
        td.warnings {color: #F00; font-weight: bold;}
        td.warnings span {color: #FFC130;}
        td.warnings image {float: left;}        
    </style>
</head>

<body>

<?php
    include_once('logos.inc');
    $filename = '../searchplugins.json';
    $jsondata = file_get_contents($filename);
    $jsonarray = json_decode($jsondata, true);

    $products = array('browser', 'mobile');
    $productnames = array('Firefox Desktop', 'Firefox Mobile (Android)');

    $locales = array('ach', 'af', 'ak', 'an', 'ar', 'as', 'ast', 'be', 'bg', 'bn-BD',
        'bn-IN', 'br', 'bs', 'ca', 'cs', 'csb', 'cy', 'da', 'de', 'el',
        'en-GB', 'en-US', 'en-ZA', 'eo', 'es-AR', 'es-CL', 'es-ES', 'es-MX', 'et', 'eu', 'fa',
        'ff', 'fi', 'fr', 'fy-NL', 'ga-IE', 'gd', 'gl', 'gu-IN', 'he', 'hi-IN',
        'hr', 'hu', 'hy-AM', 'id', 'is', 'it', 'ja', 'ja-JP-mac', 'ka', 'kk',
        'km', 'kn', 'ko', 'ku', 'lg', 'lij', 'lt', 'lv', 'mai', 'mk', 'ml', 'mr',
        'ms', 'my', 'nb-NO', 'ne-NP', 'nl', 'nn-NO', 'nr', 'nso', 'oc', 'or',
        'pa-IN', 'pl', 'pt-BR', 'pt-PT', 'rm', 'ro', 'ru', 'rw', 'si', 'sk',
        'sl', 'son', 'sq', 'sr', 'ss', 'st', 'sv-SE', 'sw', 'ta', 'ta-LK', 'te',
        'th', 'tn', 'tr', 'ts', 'uk', 've', 'vi', 'wo', 'xh', 'zh-CN', 'zh-TW',
        'zu');

    $html_output = '';
    foreach ($products as $i=>$product) {
        $channel = "aurora";
        $html_output .= "<h1>" . $productnames[$i] . ' (' . $channel . ")</h1>\n";

        $html_output .= '<table>
                <thead>
                    <tr>
                        <th>Locale</th>
                        <th>Icon</th>
                        <th>Name</th>
                        <th>Description</th>
                        <th>Warnings</th>
                    </tr>
                </thead>
                <tbody>' . "\n";

        foreach ($locales as $locale) {
            if (array_key_exists($product, $jsonarray[$locale])) {
                // I have searchplugin for this locale
                foreach ($jsonarray[$locale][$product][$channel] as $singlesp) {
                    $warnings = '';
                    $keyname = '';
                    $spfilename = strtolower($singlesp['file']);
                    if (strpos($spfilename, 'amazon') !== false) {
                        $keyname = 'amazon_' . $product;
                    } elseif (strpos($spfilename, 'ebay') !== false) {
                        $keyname = 'ebay_' . $product;
                    } elseif (strpos($spfilename, 'google') !== false) {
                        $keyname = 'google_' . $product;
                    } elseif (strpos($spfilename, 'twitter') !== false) {
                        $keyname = 'twitter_' . $product;
                    } elseif (strpos($spfilename, 'wikipedia') !== false) {
                        $keyname = 'wikipedia_' . $product;
                        if ((strpos($singlesp['description'], '(en-US)') === false) && ($locale != 'en-US') &&
                            ((strpos($singlesp['url'], 'Special:Search') !== false) || (strpos($singlesp['url'], ':Search') !== false))) {
                            # If locales is not en-US, or locale is not using en-US wikipedia                            
                                $warnings .= '<span>Could be using a non localized search URL (check ' . 
                                             '<a href="' . $singlesp['url'] . '">URL</a>).</span><br/>';                                
                        }
                        if (strpos($singlesp['url'], '%')) {
                            $warnings .= 'Searchplugin should use UTF-8 URL.<br/>';
                        }

                    } elseif (strpos($spfilename, 'yahoo') !== false) {
                        $keyname = 'yahoo_' . $product;
                    }

                    if ($keyname != '') {
                        if ($singlesp['image'] != $enUS_images[$keyname]) {
                            $warnings .= '<img src="' . $enUS_images[$keyname] . '" alt="" title="Reference Logo" /> Image is outdated.';
                        }
                    }

                    $html_output .= '                   <tr>
                      <td>' . $locale . '</td>
                      <td><img src="' . $singlesp['image'] . '" alt="searchplugin icon" /></td>' . "\n";
                        if ( $singlesp['name'] == 'not available') {
                            $html_output .=  '                      <td>' . $singlesp['name'] . ' (' . $singlesp['file'] . ")</td>\n";
                        } else {
                            $html_output .=  '                      <td>' . $singlesp['name'] . ' (' . $singlesp['file'] . ")</td>\n";
                        }
                        if ( strpos($singlesp['description'], 'not available')) {
                            $html_output .=  '                      <td>' . $singlesp['description'] . "</td>\n";
                        } else {
                            $html_output .=  '                      <td>' . $singlesp['description'] . "</td>\n";
                        }
                        if ($warnings != '') {
                            $html_output .=  '                      <td class="warnings">' . $warnings . "</td>\n</tr>\n";
                        } else {
                            $html_output .=  "                      <td>&nbsp;</td>\n</tr>\n";
                        }
                }
            }
        }

        $html_output .= "</tbody>
                </table>
            ";
    }

    echo $html_output;
    echo '<p id="update">Last update: ' . date ("Y-m-d H:i", filemtime($filename)) . '</p>';
