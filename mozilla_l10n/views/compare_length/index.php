<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset=utf-8>
    <title>Compare string length</title>
    <link rel="stylesheet" href="css/theme.ice.css">
    <script type="text/javascript" src="js/jquery-2.0.3.min.js"></script>
    <script type="text/javascript" src="js/jquery.tablesorter.min.js"></script>
    <script tpye="text/javascript">
        $(function(){
          $("#maintable").tablesorter({
            theme : 'ice'
          });
        });
    </script>
    <style>
        table td { text-align: center; }
        table th { font-weight: bold !important; text-align: center;}
    </style>
</head>

<body>

<?php
    $filename = 'stats.json';
    $jsondata = file_get_contents($filename);
    $jsonarray = json_decode($jsondata, true);
    $buckets = ['global', 'short', 'middle', 'long', 'sentence'];

    $html_output = '<table id="maintable" class="tablesorter">
                <thead>
                    <tr>
                        <th class="sorter-false">Locale</th>
                        <th class="sorter-false" colspan="3">Global</th>
                        <th class="sorter-false" colspan="3">Short<br/>(length&lt;5)</th>
                        <th class="sorter-false" colspan="3">Middle<br/>(6&lt;length&lt;11)</th>
                        <th class="sorter-false" colspan="3">Long<br/>(11&lt;length&lt;21)</th>
                        <th class="sorter-false" colspan="3">Sentence<br/>(length&gt;20)</th>
                    </tr>
                    <tr>
                        <th>&nbsp;</th>
                        <th title="number of strings analyzed">strings</th>
                        <th title="average difference in chars">avg<br/>diff<br/>chars</th>
                        <th title="average difference in percentage">avg<br/>diff<br/>%</th>
                        <th title="number of strings analyzed">strings</th>
                        <th title="average difference in chars">avg<br/>diff<br/>chars</th>
                        <th title="average difference in percentage">avg<br/>diff<br/>%</th>
                        <th title="number of strings analyzed">strings</th>
                        <th title="average difference in chars">avg<br/>diff<br/>chars</th>
                        <th title="average difference in percentage">avg<br/>diff<br/>%</th>
                        <th title="number of strings analyzed">strings</th>
                        <th title="average difference in chars">avg<br/>diff<br/>chars</th>
                        <th title="average difference in percentage">avg<br/>diff<br/>%</th>
                        <th title="number of strings analyzed">strings</th>
                        <th title="average difference in chars">avg<br/>diff<br/>chars</th>
                        <th title="average difference in percentage">avg<br/>diff<br/>%</th>
                    </tr>
                </thead>
                <tbody>' . "\n";

    foreach ($jsonarray as $locale_code => $locale){
        $html_output .= "<tr>
        <td>{$locale_code}</td>
        ";
        foreach ($buckets as $bucket) {
            $html_output .= '<td>' . $locale[$bucket]['count'] .'</td>
                             <td>' . sprintf("%01.2f", $locale[$bucket]['avg_chars']) . '</td>
                             <td>' . sprintf("%01.2f", $locale[$bucket]['avg_perc']) . '</td>';
        }
        $html_output .= '</tr>';
    }


    $html_output .= "</tbody>
            </table>
            <p>Json source file: <a href='stats.json'>link</a></p>
            <p>Script used to generate json data: <a href='https://github.com/flodolo/scripts/blob/master/mozilla_l10n/compare_string_length.py'>link</a></p>
        ";
    echo $html_output;
