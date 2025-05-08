<!doctype html>
<html lang="en">
<head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>RGZ - uvoz ulica</title>

    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css" integrity="sha384-xOolHFLEh07PJGoPkLv1IbcEPTNtaed2xpHsD9ESMhqIYd0nLMwNLD69Npy4HI+N" crossorigin="anonymous">
    <link rel="stylesheet" href="https://cdn.datatables.net/1.10.18/css/dataTables.bootstrap4.min.css" crossorigin="anonymous">
	<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
	<style>
        iframe#hiddenIframe {
            display: none;
            position: absolute;
        }

        .copy-btn {
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 5px 10px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            font-size: 14px;
            transition: background-color 0.2s;
        }

        .copy-btn:hover {
            background-color: #e0e0e0;
        }

        .copy-btn svg {
            margin-right: 5px;
            width: 16px;
            height: 16px;
        }

        .copy-icon {
            width: 24px;
            height: 24px;
            cursor: pointer;
            color: #555;
        }

        .copy-icon:hover {
            color: #000;
        }

        .success-message {
            color: green;
            font-size: 12px;
            margin-left: 10px;
            opacity: 0;
            transition: opacity 0.3s;
        }

        .show-message {
            opacity: 1;
        }
	</style>
</head>
<body>

<nav class="navbar navbar-expand-md navbar-dark bg-dark">
	<a class="navbar-brand" href="#">Uvoz RGZ ulica u OSM</a>
	<button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarsExample03" aria-controls="navbarsExample03" aria-expanded="false" aria-label="Toggle navigation">
	<span class="navbar-toggler-icon"></span>
	</button>

	<div class="collapse navbar-collapse" id="navbarsExample03">
	<ul class="navbar-nav mr-auto">
		<li class="nav-item">
			<a class="nav-link" href="https://dina.openstreetmap.rs/ar/">Početna</a>
		</li>
		<li class="nav-item">
			<a class="nav-link" href="https://dina.openstreetmap.rs/">DINA platforma</a>
		</li>
		<li class="nav-item">
			<a class="nav-link" href="https://openstreetmap.rs/obelezavanje-naziva-ulica-i-povezivanje-sa-adresnim-registrom/">Uputstvo</a>
		</li>
		<li class="nav-item">
			<a class="nav-link" href="https://community.openstreetmap.org/t/povezivanje-ulica-u-osm-sa-zvanicnim-registrom-ulica/93564">Forum</a>
		</li>
		<li class="nav-item">
			<a class="nav-link" href="https://metrics.improveosm.org/named-roads/total-metrics-per-interval?duration=weekly&locationType=country&locationId=191&unit=km&from=2016-02-14&to={{ currentDate }}">Progress</a>
		</li>
		<li class="nav-item">
			<a class="nav-link" href="https://gitlab.com/osm-serbia/adresniregistar">Github</a>
		</li>
		<li>
			<a class="nav-link" href="" data-toggle="modal" data-target="#exampleModal">Pomoć</a>
		</li>
	</ul>
	</div>
</nav>


<main role="main" class="pt-3 container-fluid">
{% block body %}{% endblock %}
</main>

<footer class="footer">
	<div class="container-fluid py-1 mt-3 mb-0 bg-light">
		<small class="text-secondary text-center">
			Data &copy; <a href="https://opendata.geosrbija.rs/">RGZ</a> &amp; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, <br/>
			RGZ podaci od {{ rgzDataDate }}, OSM podaci od {{ osmDataDate }}, izveštaj generisan u {{ reportDate }}
		</small>
	</div>
</footer>

</body>
</html>
