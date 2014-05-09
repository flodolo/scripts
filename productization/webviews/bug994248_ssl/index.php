<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset=utf-8>
    <title>Check SSL on handlers + Yahoo</title>
    <style type="text/css">
        body { background-color: #FCFCFC; font-family: Arial, Verdana; font-size: 14px; padding: 10px; }
        p { margin-top: 2px; }
        h2 { clear: both; }
        .green { color: green; }
        .red { color: red; }
    </style>
</head>

<body>

<?php
    include_once('../locales.inc');
    $filename = '../searchplugins.json';

    $jsondata = file_get_contents($filename);
    $jsonarray = json_decode($jsondata, true);

    $channel = 'aurora';
    $products = array('browser', 'mobile');
    $productnames = array('Firefox Desktop', 'Firefox Mobile (Android)');
    echo "<p>Last update: {$jsonarray['creation_date']}</p>\n";

    $html_errors = '<h1>Errors</h1><ul>';
    $html_output = '';

    foreach ($products as $i=>$product) {
        $html_output .= "<h1>Details</h1>\n<h2>{$product} - {$channel}</h2>";
        $locale_list = '';
        $nonen_locale_list = '';
        $locale_errors = [];
        foreach ($locales as $locale) {
            $html_output .= "<h3>{$locale}</h3>";
            if (array_key_exists($product, $jsonarray[$locale])) {
                if (array_key_exists($channel, $jsonarray[$locale][$product])) {
                    // I have searchplugins for this locale
                    foreach ($jsonarray[$locale][$product][$channel] as $key => $singlesp) {
                        if ($key != 'p12n') {
                            $spfilename = strtolower($singlesp['file']);
                            if (strpos($spfilename, 'yahoo') !== false) {
                                $locale_list .= "{$locale}, ";
                                if (strpos($singlesp['description'], 'en-US') === false) {
                                    $nonen_locale_list .= "{$locale}, ";
                                }
                                if (array_key_exists(2, $jsonarray[$locale][$product][$channel]['p12n']['searchorder'])) {
                                    $second_search = strtolower($jsonarray[$locale][$product][$channel]['p12n']['searchorder'][2]);
                                    if (strpos($second_search, 'yahoo') === false) {
                                        $html_output .= "<p>{$locale} doesn't have Yahoo as second ({$second_search})</p>";
                                    }
                                } else {
                                   $html_output .= "<p>{$locale} doesn't have a second search plugin</p>";
                                }
                            }

                            if (strpos($singlesp['url'], 'yahoo') !== false ||
                                strpos($singlesp['url'], 'google') !== false) {
                                if (strpos($spfilename, 'metrofx') === false) {
                                    $html_output .= "<p>{$singlesp['name']} (search): ";
                                    if (! $singlesp['secure']) {
                                        $html_output .= "<span class='red'>not SSL</span></p>";
                                        array_push($locale_errors, $locale);
                                        $html_errors .= "<li>{$locale} - {$product}: {$singlesp['name']} ({$singlesp['file']}), not SSL</li>";
                                    } else {
                                        $html_output .= "<span class='green'>SSL</span></p>";
                                    }
                                }
                            }
                        } else {
                            // Check productization for Google and Yahoo
                            if (array_key_exists('mailto', $singlesp['contenthandlers'])) {
                                $contenthandlers = $singlesp['contenthandlers']['mailto'];
                                foreach ($contenthandlers as $contenthandler) {
                                    if (strpos($contenthandler['uri'], 'yahoo') !== false ||
                                        strpos($contenthandler['uri'], 'google') !== false) {
                                        $html_output .= "<p>{$contenthandler['name']} (mailto): ";
                                        if ((strpos($contenthandler['uri'], 'https') === false)) {
                                            $html_output .= "<span class='red'>not SSL</span></p>";
                                            $html_errors .= "<li>{$locale} - {$product}: {$contenthandler['name']}, not SSL</li>";
                                            array_push($locale_errors, $locale);
                                        } else {
                                            $html_output .= "<span class='green'>SSL</span></p>";
                                        }
                                    }
                                }
                            } else {
                                $html_output .= "<p class='red'>mailto handler is missing</p>";
                                $html_errors .= "<li>{$locale} - {$product}: mailto handler is missing</li>";
                            }

                            // 30 boxes
                            if (array_key_exists('webcal', $singlesp['contenthandlers'])) {
                                $contenthandlers = $singlesp['contenthandlers']['webcal'];
                                foreach ($contenthandlers as $contenthandler) {
                                    if (strpos($contenthandler['uri'], '30boxes') !== false) {
                                        $html_output .= "<p>{$contenthandler['name']} (webcal): ";
                                        if ((strpos($contenthandler['uri'], 'https') === false)) {
                                            $html_output .= "<span class='red'>not SSL</span></p>";
                                            $html_errors .= "<li>{$locale} - {$product}: {$contenthandler['name']}, not SSL</li>";
                                            array_push($locale_errors, $locale);
                                        } else {
                                            $html_output .= "<span class='green'>SSL</span></p>";
                                        }
                                    }
                                }
                            } else {
                                $html_output .= "<p class='red'>webcal handler is missing</p>";
                                $html_errors .= "<li>{$locale} - {$product}: webcal handler is missing</li>";
                            }

                            if (array_key_exists('feedhandlers', $singlesp)) {
                                $feedhandlers = $singlesp['feedhandlers'];
                                foreach ($feedhandlers as $feedhandler) {
                                    if (strpos($feedhandler['uri'], 'yahoo') !== false ||
                                        strpos($feedhandler['uri'], 'google') !== false) {
                                        $html_output .= "<p>{$feedhandler['title']} (feed): ";
                                        if ((strpos($feedhandler['uri'], 'https') === false)) {
                                            $html_output .= "<span class='red'>not SSL</span></p>";
                                            $html_errors .= "<li>{$locale} - {$product}: {$feedhandler['title']}, not SSL</li>";
                                            array_push($locale_errors, $locale);
                                        } else {
                                            $html_output .= "<span class='green'>SSL</span></p>";
                                        }
                                    }
                                }
                            } else {
                                $html_output .= "<p class='red'>feed handler is missing</p>";
                                $html_errors .= "<li>{$locale} - {$product}: feed handler is missing</li>";
                            }
                        }
                    }
                }
            }
        }
        $html_output .= "<p>List of locales with Yahoo: {$locale_list}</p>";
        $html_output .= "<p>List of locales with localized versions of Yahoo: {$nonen_locale_list}</p>";
        $locale_errors = array_unique($locale_errors);
        if (count($locale_errors) > 0) {
            $html_output .= "<p>Locales with errors: ";
            foreach ($locale_errors as $locale) {
                $html_output .= $locale . ' ';
            }
            $html_output .= "</p>";
        }
    }

    if (count($locale_errors) > 0) {
        $html_errors .= '</ul>';
        echo $html_errors;
    }

    echo $html_output;
