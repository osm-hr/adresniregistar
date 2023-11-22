{% extends "base.html.tpl" %}
{% block body %}

<!-- Modal -->
<div class="modal fade" id="exampleModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="exampleModalLabel">Značenje kolona</h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body">
		<ul>
			<li><b>Opština</b> &mdash; Opština za koju se odnose podaci</li>
			<li><b>#RGZ (broj ulica)</b> &mdash; Ukupan broj različitih ulica u RGZ-u</li>
			<li><b>#RGZ [km]</b> &mdash; Ukupna dužina (u kilometrima) svih ulica u RGZ-u</li>
			<li><b>Konflacija [km]</b> &mdash; Ukupna dužina (u kilometrima) svih ulica u OSM-u koje su spojene sa RGZ-om (tj. imaju ispravan „ref:RS:ulica” tag)</li>
			<li><b>Konflacija [%]</b> &mdash; Procenat kilometraže svih ulica u OSM-u koje su spojene sa RGZ-om</li>
			<li><b>Pronađeno [km]</b> &mdash; Ukupna dužina (u kilometrima) svih ulica u OSM-u koje su potencijalni kandidati za spajanje sa RGZ-om</li>
			<li><b>Pronađeno [%]</b> &mdash; Procenat kilometraže svih ulica u OSM-u koje su potencijalni kandidati za spajanje sa RGZ-om (ovo znači da generalno neka ulica u blizini postoji u OSM-u, ali ne mora da znači da je to baš ulica iz RGZ-a)</li>
			<li><b>Nepronađeno [km]</b> &mdash; Preostala dužina (u kilometrima) ulica koje nisu nađene (dakle, razlika između RGZ kilometraže i OSM kilometraže)</li>
			<li><b>Nepronađeno [%]</b> &mdash; Procenat kilometraže ulica koje nisu nađene</li>
		</ul>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal">Zatvori</button>
      </div>
    </div>
  </div>
</div>

<nav aria-label="breadcrumb">
  <ol class="breadcrumb">
    <li class="breadcrumb-item" aria-current="page"><a href="../index.html">DINA</a></li>
    <li class="breadcrumb-item" aria-current="page"><a href="index.html">Ulice</a></li>
    <li class="breadcrumb-item" aria-current="page">Izveštaj</li>
  </ol>
</nav>
    <!-- Optional JavaScript -->
    <!-- jQuery first, then Popper.js, then Bootstrap JS -->
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>
    <script src="https://cdn.datatables.net/1.10.18/js/jquery.dataTables.min.js" crossorigin="anonymous"></script>
    <script src="https://cdn.datatables.net/1.10.18/js/dataTables.bootstrap4.min.js" crossorigin="anonymous"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
    <script>
	$(document).ready( function () {
	    $('#list').DataTable({
		    stateSave: true,
		    order: [[0, 'asc']],
		    lengthMenu: [ [10, 100, -1], [10, 50, "All"] ],
		    columnDefs: [
		        { targets: [2, 3, 4, 5], className: 'text-right' }
		    ]
		});
	} );
    </script>
    <script src="opstine.js"></script>
    <script>
		function onEachFeature(feature, layer) {
			let percentage = feature.properties.ratio !== null ? feature.properties.ratio.toFixed(2) : '/';
			let popupContent = `<p>${feature.properties.opstina_imel} (${percentage}%)</p>`;
			layer.bindPopup(popupContent);
		}

		function loadMap() {
			const map = L.map('map').setView([44.5, 20.5], 7);
			const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
				maxZoom: 19,
				attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
			}).addTo(map);

			const opstinelLayer = L.geoJSON(opstine, {
				style(feature) {
					value = feature.properties.ratio !== null ? feature.properties.ratio.toFixed() : 0;
					if (value > 100) {
						value = 100;
					}
					value = (255 * value) / 100; // scale from 0-100 to 0-255
					return {
						opacity: 1,
						color: 'rgba(0,0,0,1.0)',
						dashArray: '',
						lineCap: 'butt',
						lineJoin: 'miter',
						weight: 0.3,
						fill: true,
						fillOpacity: 1,
						fillColor: `rgba(255, ${255 - value}, ${255 - value}, 0.7)`,
						interactive: true,
					};
				},
				onEachFeature
			}).addTo(map);
		}

		$(document).ready( function () {
			loadMap();
		});
    </script>

<h2>Izveštaj po opštinama</h2>
<br/>
<p>Ovde možete videti statistike po opštinama. Klikom na opštinu dobijate podatke za tu opštinu. U gornjem desnom uglu je filtriranje. Kliknite na <a href="" data-toggle="modal" data-target="#exampleModal">„Pomoć”</a> u gornjem meniju da razumete kako da tumačite kolone u ovoj tabeli.</p>
Ispod tabele možete da nađete interaktivnu mapu sa prikazom procenta konflacije po opštinama.
<br/>
<br/>

<table id="list" class="table table-sm table-striped table-bordered table-hover w-100">
<thead class="thead-dark sticky-top">
	<tr>
		<th>Opština</th>
		<th>#RGZ (broj ulica)</th>
		<th>#RGZ [km]</th>
		<th class="d-sm-table-cell">Konflacija [km]</th>
		<th class="d-sm-table-cell">Konflacija [%]</th>
		<th class="d-lg-table-cell">Pronađeno [km]</th>
		<th class="d-lg-table-cell">Pronađeno [%]</th>
		<th class="d-lg-table-cell">Nepronađeno [km]</th>
		<th class="d-lg-table-cell">Nepronađeno [%]</th>
	</tr>
</thead>
<tbody>
	{% for opstina in opstine %}
	<tr>
		<td><a href="opstine/{{ opstina.name }}.html">{{ opstina.name }}</a></td>
		<td>{{ opstina.rgz }}</td>
		<td>{{ '{0:0.2f}'.format(opstina.rgz_length / 1000.0) }}</td>
		<td>{{ '{0:0.2f}'.format(opstina.conflated_length / 1000.0) }}</td>
		<td>{{ '{0:0.2f}'.format((100.0 * opstina.conflated_length) / opstina.rgz_length) }}</td>
		<td>{{ '{0:0.2f}'.format(opstina.found_length / 1000.0) }}</td>
		<td>{{ '{0:0.2f}'.format((100.0 * opstina.found_length) / opstina.rgz_length) }}</td>
		<td>{{ '{0:0.2f}'.format(opstina.notfound_length / 1000.0) }}</td>
		<td>{{ '{0:0.2f}'.format((100.0 * opstina.notfound_length) / opstina.rgz_length) }}</td>
	</tr>
	{% endfor %}
</tbody>
<tfoot>
	<tr>
		<th>Serbia TOTAL:</th>
		<th class="d-sm-table-cell">{{ total.rgz }}</th>
		<th class="d-sm-table-cell">{{ '{0:0.2f}'.format(total.rgz_length / 1000.0) }}</th>
		<th class="d-sm-table-cell">{{ '{0:0.2f}'.format(total.conflated_length / 1000.0) }}</th>
		<th class="d-sm-table-cell">{{ '{0:0.2f}'.format((100.0 * total.conflated_length) / total.rgz_length) }}</th>
		<th class="d-lg-table-cell">{{ '{0:0.2f}'.format(total.found_length / 1000.0) }}</th>
		<th class="d-sm-table-cell">{{ '{0:0.2f}'.format((100.0 * total.found_length) / total.rgz_length) }}</th>
		<th class="d-lg-table-cell">{{ '{0:0.2f}'.format(total.notfound_length / 1000.0) }}</th>
		<th class="d-sm-table-cell">{{ '{0:0.2f}'.format((100.0 * total.notfound_length) / total.rgz_length) }}</th>
	</tr>
</tfoot>
</table>

<br/><br/>
<div id="map" class="mx-auto" style="position: relative;border: 1px solid black;border-radius: 8px;height: 400px;width: min(90%, 600px);">
</div>

{% endblock %}
