{% extends "base.html.tpl" %}
{% block body %}

<!-- Modal -->
<div class="modal fade" id="exampleModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="exampleModalLabel">Značenje kolona</h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body" modal-dialog-scrollable>
        <h5>Analiza po dužini:</h5>
		<ul>
			<li><b>Naselje</b> &mdash; Naselje za koje se odnose podaci</li>
			<li><b>#RGZ [km]</b> &mdash; Ukupna dužina (u kilometrima) svih ulica u RGZ-u, uključujući i zaseoke</li>
			<li><b>RGZ konflacija [km]</b> &mdash; Ukupna dužina (u kilometrima) svih delova ulica RGZ-a koje su spojene sa OSM-om. Ukoliko je ovaj broj manji od dužine RGZ ulice, postoji delovi RGZ ulice koji nisu spojeni u OSM-u</li>
			<li><b>RGZ konflacija [%]</b> &mdash; Procenat kilometraže svih ulica RGZ-a koje su spojene sa OSM-om</li>
			<li><b>OSM konflacija [km]</b> &mdash; Ukupna dužina (u kilometrima) svih ulica u OSM-u koje su spojene sa RGZ-om (tj. imaju ispravan „ref:RS:ulica” tag)</li>
			<li><b>OSM konflacija [%]</b> &mdash; Procenat kilometraže svih ulica u OSM-u koje su spojene sa RGZ-om</li>
			<li><b>Pronađeno [km]</b> &mdash; Ukupna dužina (u kilometrima) svih ulica u OSM-u koje su potencijalni kandidati za spajanje sa RGZ-om (ovo znači da generalno neka ulica u blizini postoji u OSM-u, ali ne mora da znači da je to baš ulica iz RGZ-a)</li>
			<li><b>Pronađeno [%]</b> &mdash; Procenat kilometraže svih ulica u OSM-u koje su potencijalni kandidati za spajanje sa RGZ-om</li>
			<li><b>Nepronađeno [km]</b> &mdash; Preostala dužina (u kilometrima) ulica koje nisu nađene (dakle, razlika između RGZ kilometraže i OSM kilometraže). Ovim se ukazuje da verovatno ništa oko ove ulice nije ni ucrtano u OSM-u</li>
			<li><b>Nepronađeno [%]</b> &mdash; Procenat kilometraže ulica koje nisu nađene</li>
		</ul>
	    <h5>Analiza po broju:</h5>
	    <ul>
			<li><b>Naselje</b> &mdash; Naselje za koje se odnose podaci</li>
			<li><b>#RGZ (broj ulica)</b> &mdash; Ukupan broj različitih ulica u RGZ-u, bez zaseoka i ulica koje geometrijom podsećaju na zaseoke</li>
			<li><b>Konflacija (bar jedan way)</b> &mdash; Ukupna broj RGZ ulica koje imaju bar jedan segment (jedan OSM way) spojen sa RGZ-om (tj. imaju ispravan „ref:RS:ulica” tag)</li>
			<li><b>Konflacija [%]</b> &mdash; Procenat svih ulica u RGZ-u kojima je bar jedan segment spojen sa RGZ-om</li>
			<li><b>Pronađeno (bar jedan way)</b> &mdash; Ukupan broj svih ulica u RGZ-u koje imaju bar jednog potencijalnog kandidata za spajanje sa RGZ-om (ovo znači da generalno neka ulica u blizini postoji u OSM-u, ali ne mora da znači da je to baš ulica iz RGZ-a)</li>
			<li><b>Pronađeno [%]</b> &mdash; Procenat svih ulica u RGZ-u koje imaju bar jednog potencijalnog kandidata za spajanje sa RGZ-om</li>
			<li><b>Nepronađeno (bar jedan way)</b> &mdash; Ukupan broj ulica iz RGZ-a koje nemaju nijednog kandidata za spajanje sa RGZ-om (dakle, razlika između ukupnih iz RGZ-a i zbira spojenih i pronađenih). Ovim se ukazuje da verovatno ništa oko ove ulice nije ni ucrtano u OSM-u</li>
			<li><b>Nepronađeno [%]</b> &mdash; Procenat broja ulica iz RGZ-a koje nemaju nijednog kandidata za spajanje sa RGZ-om</li>
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
    <li class="breadcrumb-item" aria-current="page"><a href="../../index.html">DINA</a></li>
    <li class="breadcrumb-item" aria-current="page"><a href="../index.html">Ulice</a></li>
    <li class="breadcrumb-item" aria-current="page"><a href="../report.html">Izveštaj</a></li>
    <li class="breadcrumb-item active" aria-current="page">{{ opstina.name }}</li>
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
	    $('#list-by-length').DataTable({
		    stateSave: true,
		    order: [[0, 'asc']],
		    lengthMenu: [ [10, 100, -1], [10, 50, "All"] ],
		    columnDefs: []
		});
	    $('#list-by-count').DataTable({
		    stateSave: true,
		    order: [[0, 'asc']],
		    lengthMenu: [ [10, 100, -1], [10, 50, "All"] ],
		    columnDefs: []
		});
	} );
    </script>
    <script src="{{ opstina.name_norm }}.js"></script>
    <script>
		function onEachFeature(feature, layer) {
			let percentage = feature.properties.ratio !== null ? feature.properties.ratio.toFixed(2) : '/';
			let popupContent = `<p>${feature.properties.naselje_imel} (${percentage}%)</p>`;
			layer.bindPopup(popupContent);
		}

		function loadMap() {
			const map = L.map('map').setView([44.5, 21], 7);
			const tiles = L.tileLayer('https://tiles.openstreetmap.rs/cir/{z}/{x}/{y}.png', {
				maxZoom: 19,
				minZoom: 7,
				attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
			}).addTo(map);
			var sw = L.latLng(42, 18.5);
			var ne = L.latLng(46.5, 23.5);
			var bounds = L.latLngBounds(sw, ne);
			map.setMaxBounds(bounds);
			map.on('drag', function() {
				map.panInsideBounds(bounds, { animate: false });
			});

			const naseljeLayer = L.geoJSON(naselja, {
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
			map.fitBounds([
				[{{ opstina.bounds.1 }}, {{ opstina.bounds.0 }}],
				[{{ opstina.bounds.3 }}, {{ opstina.bounds.2 }}]
			]);
		}

		$(document).ready( function () {
			loadMap();
		});
    </script>

<h2>Izveštaj po naseljima</h2>
<br/>

<p>
Ovde možete videti statistike po naselju u okviru opštine „{{ opstina.name }}”.
Klikom na naselje dobijate podatke za to naselje.
U gornjem desnom uglu je filtriranje. Kliknite na <a href="" data-toggle="modal" data-target="#exampleModal">„Pomoć”</a> u gornjem meniju da razumete kako da tumačite kolone u ovoj tabeli.</p>

<p>Dostupne su dve analize &ndash; jedna gleda ukupno pokrivene kilometre puta koji su povezani sa RGZ-om („Analiza po dužini”), dok druga pokriva slučajeve kada je bar jedna RGZ ulica povezana („Analiza po broju”).</p>
<p>Ispod tabele možete da nađete interaktivnu mapu opštine „{{ opstina.name }}” sa prikazom procenta konflacije po naseljima za analizu po dužini.</p>
<br/>
<br/>

<ul class="nav nav-pills mb-3" id="pills-tab" role="tablist">
  <li class="nav-item" role="presentation">
    <button class="nav-link active" id="pills-by-length-tab" data-toggle="pill" data-target="#pills-by-length" type="button" role="tab" aria-controls="pills-by-length" aria-selected="true">Analiza po dužini</button>
  </li>
  <li class="nav-item" role="presentation">
    <button class="nav-link" id="pills-by-count-tab" data-toggle="pill" data-target="#pills-by-count" type="button" role="tab" aria-controls="pills-by-count" aria-selected="false">Analiza po broju</button>
  </li>
</ul>
<div class="tab-content" id="pills-tabContent">
  <div class="tab-pane fade show active" id="pills-by-length" role="tabpanel" aria-labelledby="pills-by-length-tab">
    <table id="list-by-length" class="table table-sm table-striped table-bordered table-hover" style="width:100%">
      <thead class="thead-dark sticky-top">
        <tr>
            <th>Naselje</th>
            <th>#RGZ [km]</th>
            <th class="d-sm-table-cell">RGZ konflacija [km]</th>
            <th class="d-sm-table-cell">RGZ konflacija [%]</th>
            <th class="d-sm-table-cell">OSM konflacija [km]</th>
            <th class="d-sm-table-cell">OSM konflacija [%]</th>
            <th class="d-lg-table-cell">Pronađeno [km]</th>
            <th class="d-lg-table-cell">Pronađeno [%]</th>
            <th class="d-lg-table-cell">Nepronađeno [km]</th>
            <th class="d-lg-table-cell">Nepronađeno [%]</th>
        </tr>
      </thead>
      <tbody>
        {% for naselje in naselja %}
        <tr>
            <td><a href="{{ opstina.name_norm }}/{{ naselje.name_lat }}.html">{{ naselje.name_lat }}</a></td>
            <td>{{ '{0:0.1f}'.format(naselje.rgz_length / 1000.0).replace('.', ',') }}</td>
            <td>{{ '{0:0.1f}'.format(naselje.conflated_length_rgz / 1000.0).replace('.', ',') }}</td>
            <td>{{ '{0:0.2f}'.format((100.0 * naselje.conflated_length_rgz) / naselje.rgz_length).replace('.', ',') if naselje.rgz_length > 0 else '/' }}</td>
            <td>{{ '{0:0.1f}'.format(naselje.conflated_length / 1000.0).replace('.', ',') }}</td>
            <td>{{ '{0:0.2f}'.format((100.0 * naselje.conflated_length) / naselje.rgz_length).replace('.', ',') if naselje.rgz_length > 0 else '/' }}</td>
            <td>{{ '{0:0.1f}'.format(naselje.found_length / 1000.0).replace('.', ',') }}</td>
            <td>{{ '{0:0.2f}'.format((100.0 * naselje.found_length) / naselje.rgz_length).replace('.', ',') if naselje.rgz_length > 0 else '/' }}</td>
            <td>{{ '{0:0.1f}'.format(naselje.notfound_length / 1000.0).replace('.', ',') }}</td>
            <td>{{ '{0:0.2f}'.format((100.0 * naselje.notfound_length) / naselje.rgz_length).replace('.', ',') if naselje.rgz_length > 0 else '/' }}</td>
        </tr>
        {% endfor %}
      </tbody>
      <tfoot>
        <tr>
            <th>{{ opstina.name }} TOTAL:</th>
            <th class="d-sm-table-cell">{{ '{0:0.1f}'.format(opstina.rgz_length / 1000.0).replace('.', ',') }}</th>
            <th class="d-sm-table-cell">{{ '{0:0.1f}'.format(opstina.conflated_length_rgz / 1000.0).replace('.', ',') }}</th>
            <th class="d-sm-table-cell">{{ '{0:0.2f}'.format((100.0 * opstina.conflated_length_rgz) / opstina.rgz_length).replace('.', ',') if opstina.rgz_length > 0 else '/' }}</th>
            <th class="d-sm-table-cell">{{ '{0:0.1f}'.format(opstina.conflated_length / 1000.0).replace('.', ',') }}</th>
            <th class="d-sm-table-cell">{{ '{0:0.2f}'.format((100.0 * opstina.conflated_length) / opstina.rgz_length).replace('.', ',') if opstina.rgz_length > 0 else '/' }}</th>
            <th class="d-sm-table-cell">{{ '{0:0.1f}'.format(opstina.found_length / 1000.0).replace('.', ',') }}</th>
            <th class="d-sm-table-cell">{{ '{0:0.2f}'.format((100.0 * opstina.found_length) / opstina.rgz_length).replace('.', ',') if opstina.rgz_length > 0 else '/' }}</th>
            <th class="d-sm-table-cell">{{ '{0:0.1f}'.format(opstina.notfound_length / 1000.0).replace('.', ',') }}</th>
            <th class="d-sm-table-cell">{{ '{0:0.2f}'.format((100.0 * opstina.notfound_length) / opstina.rgz_length).replace('.', ',') if opstina.rgz_length > 0 else '/' }}</th>
        </tr>
      </tfoot>
    </table>
  </div>
  <div class="tab-pane fade" id="pills-by-count" role="tabpanel" aria-labelledby="pills-by-count-tab">
    <table id="list-by-count" class="table table-sm table-striped table-bordered table-hover" style="width:100%">
      <thead class="thead-dark sticky-top">
        <tr>
            <th>Naselje</th>
            <th>#RGZ (broj ulica)</th>
            <th class="d-sm-table-cell">Konflacija (bar jedan way)</th>
            <th class="d-sm-table-cell">Konflacija [%]</th>
            <th class="d-lg-table-cell">Pronađeno (bar jedan way)</th>
            <th class="d-lg-table-cell">Pronađeno [%]</th>
            <th class="d-lg-table-cell">Nepronađeno (bar jedan way)</th>
            <th class="d-lg-table-cell">Nepronađeno [%]</th>
        </tr>
      </thead>
      <tbody>
        {% for naselje in naselja %}
        <tr>
            <td><a href="{{ opstina.name_norm }}/{{ naselje.name_lat }}.html">{{ naselje.name_lat }}</a></td>
            <td>{{ naselje.rgz }}</td>
            <td>{{ naselje.conflated_count }}</td>
            <td>{{ '{0:0.2f}'.format((100.0 * naselje.conflated_count) / naselje.rgz).replace('.', ',') if naselje.rgz > 0 else '/' }}</td>
            <td>{{ naselje.found_count }}</td>
            <td>{{ '{0:0.2f}'.format((100.0 * naselje.found_count) / naselje.rgz).replace('.', ',') if naselje.rgz > 0 else '/' }}</td>
            <td>{{ naselje.notfound_count }}</td>
            <td>{{ '{0:0.2f}'.format((100.0 * naselje.notfound_count) / naselje.rgz).replace('.', ',') if naselje.rgz > 0 else '/' }}</td>
        </tr>
        {% endfor %}
      </tbody>
      <tfoot>
        <tr>
            <th>{{ opstina.name }} TOTAL:</th>
            <th class="d-sm-table-cell">{{ opstina.rgz }}</th>
            <th class="d-sm-table-cell">{{ opstina.conflated_count }}</th>
            <th class="d-sm-table-cell">{{ '{0:0.2f}'.format((100.0 * opstina.conflated_count) / opstina.rgz).replace('.', ',') if opstina.rgz > 0 else '/' }}</th>
            <th class="d-sm-table-cell">{{ opstina.found_count }}</th>
            <th class="d-sm-table-cell">{{ '{0:0.2f}'.format((100.0 * opstina.found_count) / opstina.rgz).replace('.', ',') if opstina.rgz > 0 else '/' }}</th>
            <th class="d-sm-table-cell">{{ opstina.notfound_count }}</th>
            <th class="d-sm-table-cell">{{ '{0:0.2f}'.format((100.0 * opstina.notfound_count) / opstina.rgz).replace('.', ',') if opstina.rgz > 0 else '/' }}</th>
        </tr>
      </tfoot>
    </table>
  </div>
</div>

<div id="map" class="mx-auto" style="position: relative;border: 1px solid black;border-radius: 8px;height: 400px;width: min(90%, 600px);">
</div>

{% endblock %}
