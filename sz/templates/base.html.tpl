<!doctype html>
<html lang="en">
<head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Stambene zajednice</title>

    <script src="https://cdn.plot.ly/plotly-2.25.2.min.js" charset="utf-8"></script>
    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous">
    <link rel="stylesheet" href="https://cdn.datatables.net/1.10.18/css/dataTables.bootstrap4.min.css" crossorigin="anonymous">
</head>
<body>

<nav class="navbar navbar-expand-md navbar-dark bg-dark">
	<a class="navbar-brand" href="#">Stambene zajednice</a>
	<button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarsExample03" aria-controls="navbarsExample03" aria-expanded="false" aria-label="Toggle navigation">
	<span class="navbar-toggler-icon"></span>
	</button>

	<div class="collapse navbar-collapse" id="navbarsExample03">
	<ul class="navbar-nav mr-auto">
		<li class="nav-item">
			<a class="nav-link" href="https://openstreetmap.rs/download/ar/">Početna</a>
		</li>
		<li class="nav-item">
			<a class="nav-link" href="https://opendata.openstreetmap.rs/">Otvoreni podaci</a>
		</li>
		<li class="nav-item">
			<a class="nav-link" href="https://community.openstreetmap.org/t/registar-stambenih-zajednica-otvoreni-podaci/87583">Forum</a>
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
			OSM podaci od {{ osmDataDate }}, izveštaj generisan u {{ reportDate }}
		</small>
	</div>
</footer>

</body>
</html>
