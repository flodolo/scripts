<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset=utf-8>
    <title>Web Status</title>
    <style type="text/css">
        body {background-color: #FFF; font-family: Arial, Verdana; font-size: 14px; padding: 10px 30px;}
        p {margin-top: 2px;}
        div.list {background-color: #FAFAFA; padding: 6px; border: 1px solid #555; border-radius: 8px; line-height: 1.7em; font-size: 16px; width: 800px;}
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
    $file_name = 'webstatus.json';
    $file_cache = 'details.inc';

    // Read the json file
    $json_array = (array) json_decode(file_get_contents($file_name), true);

    // Check how old the cache file is
    if ((! file_exists($file_cache)) || (time() - filemtime($file_cache) >= 60*60*5)) {
        // File is older than 5 hours or doesn't exist, regenerate arrays and save it
        $available_locales = array();
        foreach (array_keys($json_array) as $locale_code) {
            $available_locales[] = $locale_code;
        }
        $available_products = array();
        $available_products[] = 'all';
        foreach ($available_locales as $locale_code) {
            foreach (array_keys($json_array[$locale_code]) as $product_code) {
                if (! in_array($product_code, $available_products)) {
                    $available_products[] = $product_code;
                }
            }
        }
        $txt_arrays = '<?php ' . PHP_EOL;
        $txt_arrays .= '$available_locales = ' . json_encode($available_locales) . ';' . PHP_EOL;
        $txt_arrays .= '$available_products = ' . json_encode($available_products) . ';' . PHP_EOL;
        file_put_contents ($file_cache, $txt_arrays);
    } else {
        // File is recent, no need to regenerate the arrays
        include_once $file_cache;
        echo '<!-- Using cached file: ' . date ('Y-m-d H:i', filemtime($file_cache)) . "-->\n";
    }

    $requested_locale = !empty($_REQUEST['locale']) ? $_REQUEST['locale'] : 'en-US';
    $requested_product = !empty($_REQUEST['product']) ? $_REQUEST['product'] : 'all';

    echo '<h1>Current locale: ' . $requested_locale . "</h1>\n";
    echo '<div class="list">
            <p>Available locales: <br/>';
    foreach ($available_locales as $locale_code) {
        echo '<a href="?locale=' . $locale_code . '">' . $locale_code . '</a>&nbsp; ';
    }
    echo "  </p>
          </div>";

    echo '<h1>Current product: ' . $requested_product . "</h1>\n";
    echo '<div class="list">
            <p>Available products: <br/>';
    foreach ($available_products as $product_code) {
        echo '<a href="?product=' . $product_code . '">' . $product_code . '</a>&nbsp; ';
    }
    echo '  </p>
          </div>';

    if ($requested_product == 'all') {
        // Display all products for one locale
        ?>
        <table>
            <thead>
                <th>Product</th>
                <th>%</th>
                <th>Translated</th>
                <th>Untransl.</th>
                <th>Fuzzy</th>
                <th>Total</th>
                <th>Errors</th>
            </thead>
            <tbody>
        <?php
        foreach ($json_array[$requested_locale] as $current_product) {
            if ($current_product['percentage'] == 100) {
                $classrow = 'complete';
            } else {
                $classrow = 'incomplete';
            }

            if ($current_product['error_status'] == 'true') {
                $classrow = 'error';
            }

            echo '<tr class="' . $classrow . '">
                    ';
            echo '<th>' . $current_product['name'] . "</th>\n";
            echo '      <td class="number">' . $current_product['percentage'] . '</td>';
            echo '      <td class="number">' . $current_product['translated'] . '</td>';
            echo '      <td class="number">' . $current_product['untranslated'] . '</td>';
            echo '      <td class="number">' . $current_product['fuzzy'] . '</td>';
            echo '      <td class="number">' . $current_product['total'] . '</td>';
            echo '      <td>' . $current_product['error_message'] . '</td>';
            echo '</tr>';
        }
        ?>
            </tbody>
        <table>
    <?php
    } else {
        // Display all locales for one product
    ?>
        <h2><?php echo $requested_product; ?></h2>
        <table>
            <thead>
                <th>Locale</th>
                <th>%</th>
                <th>Translated</th>
                <th>Untransl.</th>
                <th>Fuzzy</th>
                <th>Total</th>
                <th>Errors</th>
            </thead>
            <tbody>
        <?php
        foreach ($available_locales as $locale_code) {
            if (isset($json_array[$locale_code][$requested_product])) {
                $current_product = $json_array[$locale_code][$requested_product];
                if ($current_product['percentage'] == 100) {
                    $classrow = 'complete';
                } else {
                    $classrow = 'incomplete';
                }

                if ($current_product['error_status'] == 'true') {
                    $classrow = 'error';
                }

                echo '<tr class="' . $classrow . '">
                        ';
                echo '<th>' . $locale_code . "</th>\n";
                echo '      <td class="number">' . $current_product['percentage'] . '</td>';
                echo '      <td class="number">' . $current_product['translated'] . '</td>';
                echo '      <td class="number">' . $current_product['untranslated'] . '</td>';
                echo '      <td class="number">' . $current_product['fuzzy'] . '</td>';
                echo '      <td class="number">' . $current_product['total'] . '</td>';
                echo '      <td>' . $current_product['error_message'] . '</td>';
                echo '</tr>';
            }
        }
        ?>
            </tbody>
        <table>
    <?php
    }
    ?>

<?php
    echo '<p id="update">Last update: ' . date ("Y-m-d H:i", filemtime($file_name)) . '</p>';
?>
</body>
</html>