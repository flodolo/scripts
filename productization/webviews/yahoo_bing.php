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
        table tbody tr.fixed {background: #A5FAB0;}
        table tbody td.number {text-align: right;}
        table tbody tr.complete {background-color: #92CC6E}
        table tbody tr.incomplete {background-color: #FFA952}
        table tbody tr.error {background-color: #FF5252}
    </style>
</head>

<body>

<?php

    $jsondata = file_get_contents("searchplugins.json");
    $jsonarray = json_decode($jsondata, true);

    $products = array('browser', 'mobile');
    $productnames = array('Firefox Desktop', 'Firefox Mobile (Android)');

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
    $html_output = '';
    foreach ($products as $i=>$product) {
        $html_output .= "<h1>" . $productnames[$i] ."</h1>\n";
        $yahoo_total = $yahoo_enUS = $bing_total = $bing_enUS = 0;

        $html_output .= '<table>
                <thead>
                    <tr>
                        <th>Locale</th>
                        <th>Icon</th>
                        <th>Name</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>' . "\n";

        foreach ($locales as $locale) {
            $channel = "beta";
            if (array_key_exists($product, $jsonarray[$locale])) {
                // I have searchplugin for this locale
                foreach ($jsonarray[$locale][$product][$channel] as $singlesp) {
                    if (strpos($singlesp['file'], 'yahoo') !== false || strpos($singlesp['file'], 'bing')!== false) {
                        // Print only Yahoo and Bing

                        // Increment counters
                        if (strpos($singlesp['file'], 'yahoo') !== false) {
                            // It's Yahoo
                            $yahoo_total++;
                            if (strpos($singlesp['description'], 'en-US') !== false) {
                                // It's the en-US version
                                $yahoo_enUS++;
                            }
                        }
                        if (strpos($singlesp['file'], 'bing') !== false) {
                            // It's Bing
                            $bing_total++;
                            if (strpos($singlesp['description'], 'en-US') !== false) {
                                // It's the en-US version
                                $bing_enUS++;
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
                            $html_output .=  '                      <td>' . $singlesp['description'] . "</td></tr>\n";
                        } else {
                            $html_output .=  '                      <td>' . $singlesp['description'] . "</td>
                    </tr>\n";
                        }
                    }
                }
            }
        }
        $html_output .= "</tbody>
                </table>
            ";
        $html_output .= "<p><strong>Yahoo:</strong> {$yahoo_total} ({$yahoo_enUS} en-US)";
        $html_output .= "<p><strong>Bing:</strong> {$bing_total} ({$bing_enUS} en-US)";
    }

    echo $html_output;


