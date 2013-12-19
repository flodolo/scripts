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
                        <th class="sorter-false">&nbsp;</th>
                        <th class="sorter-false" colspan="5" title="Average values">Global</th>
                        <th class="sorter-false" colspan="5" title="Strings with 5 or less characters">Short<br/>(length ≤ 5)</th>
                        <th class="sorter-false" colspan="5" title="Strings with 6 to 10 characters">Middle<br/>(6 ≤ length ≤ 10)</th>
                        <th class="sorter-false" colspan="5" title="Strings with 11 to 20 characters">Long<br/>(11 ≤ length ≤ 20)</th>
                        <th class="sorter-false" colspan="5" title="Strings at least 21 characters">Sentence<br/>(length > 20)</th>
                    </tr>
                    <tr>
                        <th>Locale</th>
                        <th title="number of strings analyzed">strings</th>
                        <th title="average difference in chars">avg<br/>diff<br/>chars</th>
                        <th title="average difference in percentage">avg<br/>diff<br/>%</th>
                        <th title="maximum difference in chars">max<br/>diff<br/>chars</th>
                        <th title="minimum difference in chars">min<br/>diff<br/>chars</th>
                        <th title="number of strings analyzed">strings</th>
                        <th title="average difference in chars">avg<br/>diff<br/>chars</th>
                        <th title="average difference in percentage">avg<br/>diff<br/>%</th>
                        <th title="maximum difference in chars">max<br/>diff<br/>chars</th>
                        <th title="minimum difference in chars">min<br/>diff<br/>chars</th>
                        <th title="number of strings analyzed">strings</th>
                        <th title="average difference in chars">avg<br/>diff<br/>chars</th>
                        <th title="average difference in percentage">avg<br/>diff<br/>%</th>
                        <th title="maximum difference in chars">max<br/>diff<br/>chars</th>
                        <th title="minimum difference in chars">min<br/>diff<br/>chars</th>
                        <th title="number of strings analyzed">strings</th>
                        <th title="average difference in chars">avg<br/>diff<br/>chars</th>
                        <th title="average difference in percentage">avg<br/>diff<br/>%</th>
                        <th title="maximum difference in chars">max<br/>diff<br/>chars</th>
                        <th title="minimum difference in chars">min<br/>diff<br/>chars</th>
                        <th title="number of strings analyzed">strings</th>
                        <th title="average difference in chars">avg<br/>diff<br/>chars</th>
                        <th title="average difference in percentage">avg<br/>diff<br/>%</th>
                        <th title="maximum difference in chars">max<br/>diff<br/>chars</th>
                        <th title="minimum difference in chars">min<br/>diff<br/>chars</th>
                    </tr>
                </thead>
                <tbody>' . "\n";

    foreach ($jsonarray as $locale_code => $locale){
        # Filter out not interesting locales
        if (!in_array($locale_code, ['az', 'en-GB', 'sah', 'tl'])) {
            $html_output .= "<tr>
            <td>{$locale_code}</td>
            ";
            foreach ($buckets as $bucket) {
                $html_output .= '<td>' . $locale[$bucket]['count'] .'</td>
                                 <td>' . sprintf("%01.2f", $locale[$bucket]['avg_chars']) . '</td>
                                 <td>' . sprintf("%01.2f", $locale[$bucket]['avg_perc']) . '</td>
                                 <td title="' . $locale[$bucket]['max_diff_id'] . '">' . $locale[$bucket]['max_diff'] . '</td>
                                 <td title="' . $locale[$bucket]['min_diff_id'] . '">' . $locale[$bucket]['min_diff'] . '</td>';

            }
            $html_output .= '</tr>';
        }
    }


    $html_output .= "</tbody>
            </table>
            <p>String lenghts comparison based on mozilla-beta.</p>
            <p>Json source file: <a href='stats.json'>link</a></p>
            <p>Script used to generate json data: <a href='https://github.com/flodolo/scripts/blob/master/mozilla_l10n/compare_string_length.py'>link</a></p>
        ";
    echo $html_output;
