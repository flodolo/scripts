<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset=utf-8>
    <title>Web Status</title>
    <style type="text/css">
        body {background-color: #FFF; font-family: Arial, Verdana; font-size: 14px; padding: 10px 30px;}
        p {margin-top: 2px;}
        div#localelist {background-color: #FAFAFA; padding: 6px; border: 1px solid #555; border-radius: 8px; line-height: 1.7em; font-size: 16px; width: 800px;}
        table {padding: 0; margin: 0; border-collapse: collapse; color: #333; background: #F3F5F7; margin-top: 20px;}
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
        p#update {margin: 20px;}
    </style>
</head>

<body>

<?php
    date_default_timezone_set('Europe/Rome');
    $jsondata = file_get_contents("webstatus.json");
    $jsonarray = json_decode($jsondata, true);

    $locales = array(    'ach', 'af', 'ak', 'an', 'ar', 'as', 'ast', 'be', 'bg', 'bn-IN',
        'bn-BD', 'br', 'bs', 'ca', 'cs', 'csb', 'cy', 'da', 'de', 'el',
        'eo', 'es-AR', 'es-ES', 'es-CL', 'es-MX', 'et', 'eu', 'fa', 'ff',
        'fi', 'fr', 'fy-NL', 'ga-IE', 'gd', 'gl', 'gu-IN', 'he', 'hi-IN',
        'hr', 'hu', 'hy-AM', 'id', 'is', 'it', 'ja', 'ka', 'kk', 'kn', 'km',
        'ko', 'ku', 'lg', 'lij', 'lt', 'lv', 'mai', 'mk', 'ml', 'mn', 'mr',
        'ms', 'my', 'nb-NO', 'nl', 'nn-NO', 'nso', 'oc', 'or', 'pa-IN',
        'pl', 'pt-BR', 'pt-PT', 'rm', 'ro', 'ru', 'si', 'sk', 'sl', 'son',
        'sq', 'sr', 'sv-SE', 'sw', 'ta', 'ta-LK', 'te', 'th', 'tr', 'uk',
        'ur', 'vi', 'wo', 'zh-CN', 'zh-TW', 'zu');

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

    ?>
    <table>
        <thead>
            <th>Product name</th>
            <th>%</th>
            <th>Translated</th>
            <th>Untransl.</th>
            <th>Fuzzy</th>
            <th>Total</th>
            <th>Errors</th>
        </thead>
        <tbody>
    <?php
    foreach ($jsonarray[$locale] as $website) {
        if ($website['percentage'] == 100) {
            $classrow = "complete";
        } else {
            $classrow = "incomplete";
        }

        if ($website['error_status'] == 'true') {
            $classrow = 'error';
        }

        echo "<tr class='" . $classrow . "'>
                ";
        echo "<th>" . $website['name'] . "</th>\n";
        echo "      <td class='number'>" . $website['percentage'] . "</td>";
        echo "      <td class='number class='number''>" . $website['translated'] . "</td>";
        echo "      <td class='number'>" . $website['untranslated'] . "</td>";
        echo "      <td class='number'>" . $website['fuzzy'] . "</td>";
        echo "      <td class='number'>" . $website['total'] . "</td>";
        echo "      <td>" . $website['error_message'] . "</td>";
        echo "</tr>";
    }
?>
        </tbody>
    <table>

<?php
    echo "<p id='update'>Last update: " . date ("Y-m-d H:i", filemtime("webstatus.json")) . "</p>";
?>
</body>
</html>