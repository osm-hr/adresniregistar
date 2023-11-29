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
			<li><b>Id (RGZ)</b> &mdash; Identifikator ulice u RGZ-u (ono što se stavlja u „ref:RS:ulica” tag)</li>
			<li><b>Ulica (RGZ)</b> &mdash; Ime ulice iz RGZ-a, a posle strelice i pravilno ime ulice kako treba uneti u OSM. Ukoliko nema imena ulice posle strelice, znači da ulice još nema u <a href="https://dina.openstreetmap.rs/ar/street_mapping.html" target="_blank">registru</a>. Klikom na ulicu se otvara geojson.io portal na kome može da se vidi i RGZ ulica (crvenom bojom) i sve conflated OSM ulice (plavom bojom)</li>
			<li><b>Dužina (RGZ)</b> &mdash; Ukupna dužina ulice u RGZ-u (u metrima)</li>
			<li><b>Conflated putevi (dužina)</b> &mdash; Spisak svih nađenih puteva u OSM-u koji su spojeni sa RGZ ulicom preko „ref:RS:ulica” taga. Za svaki je u zagradi navedena njegova dužina u OSM-u</li>
			<li><b>Conflated - max greška (m)</b> &mdash; Najveća greška između RGZ ulice i OSM ulica (u metrima). Najveća udaljenost koju dve tačke na ovim ulicama mogu imati. Ova vrednost obično ne sme biti preko par stotina metara</li>
			<li><b>Potencijalni putevi (% poklapanja, dužina)</b> &mdash; Spisak svih potencijalno nađenih OSM puteva koje treba spojiti sa RGZ-om. Za svaki OSM put je naveden procenat poklapanja sa RGZ putem i njegova OSM dužina.
			Ukoliko je ime puta <s>precrtano</s>, to označava da se ime iz RGZ-a i ime iz OSM-a ne slažu. Ukoliko ime puta ima prefiks „✅”, to znači da se ime RGZ i OSM puta kompletno slažu. <b>PAŽNJA:</b> u ovoj koloni može biti dosta grešaka i ne unositi ovo automatizovano</li>
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
    <li class="breadcrumb-item" aria-current="page"><a href="../../../index.html">DINA</a></li>
	<li class="breadcrumb-item" aria-current="page"><a href="../../index.html">Ulice</a></li>
	<li class="breadcrumb-item" aria-current="page"><a href="../../report.html">Izveštaj</a></li>
	<li class="breadcrumb-item active" aria-current="page"><a href="../{{ opstina_name }}.html">{{ opstina_name }}</a></li>
	<li class="breadcrumb-item active" aria-current="page">{{ naselje.name_lat }}</li>
  </ol>
</nav>
    <!-- Optional JavaScript -->
    <!-- jQuery first, then Popper.js, then Bootstrap JS -->
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>
    <script src="https://cdn.datatables.net/1.10.18/js/jquery.dataTables.min.js" crossorigin="anonymous"></script>
    <script src="https://cdn.datatables.net/1.10.18/js/dataTables.bootstrap4.min.js" crossorigin="anonymous"></script>
    <script>
	$(document).ready( function () {
		$.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
		    let isConflated = $("#isConflatedSelect option:selected").val();
			let isPotential = $("#isPotentialSelect option:selected").val();

            let isConflatedFilter = true;
            if (isConflated === 'yes') {
                isConflatedFilter = data[3].indexOf('w') > -1;
            } else if (isConflated === 'no') {
                isConflatedFilter = data[3].indexOf('w') === -1;
            }

            let isPotentialFilter = true;
            if (isPotential === 'yes') {
                isPotentialFilter = data[5].indexOf('✅') > -1;
            } else if (isPotential === 'partial') {
                isPotentialFilter = data[5].indexOf('(') > -1;
            } else if (isPotential === 'errors') {
                isPotentialFilter = data[5].indexOf('<s>') > -1;
            } else if (isPotential === 'no') {
                isPotentialFilter = data[5].trim() === '';
            }

			return isConflatedFilter && isPotentialFilter;
		});


	    var table = $('#list').DataTable({
		    stateSave: true,
		    order: [[1, 'asc']],
		    lengthMenu: [ [10, 100, -1], [10, 50, "All"] ],
		    columnDefs: [
		        { targets: [2, 4], className: 'text-right' },
		    ]
		});

        $('#isConflatedSelect').on('change', function() {
            table.draw();
        });
        $('#isPotentialSelect').on('change', function() {
            table.draw();
        });
	} );
    </script>


<h2>Izveštaj za {{ naselje.name_lat }}</h2>
<br/>

<p>Ovde možete videti sve ulice unutar naselja „{{ naselje.name_lat }}” i status konflacije. U gornjem desnom uglu je filtriranje.
Podaci u poslednjoj koloni tabele prikazuju <b>samo potencijalne vrednosti</b> i treba ih koristiti samo kao savete. Potrebno je svaku ulicu otvoriti u editoru i obratiti pažnju prilikom uvoza!
</p>
	<p>
	<b>Kliknite na <a href="" data-toggle="modal" data-target="#exampleModal">„Pomoć”</a></b> u gornjem meniju da razumete kako da tumačite kolone u ovoj tabeli.
	</p>
<br/>
<br/>

<div class="text-right">
    <label for="isConflated">Conflated putevi</label>
    <select name="isConflated" id="isConflatedSelect">
      <option value="all"></option>
      <option value="yes">Da</option>
      <option value="no">Ne</option>
    </select>
    <br/>
    <label for="isPotential">Potencijalni putevi</label>
    <select name="isPotential" id="isPotentialSelect">
      <option value="all"></option>
      <option value="yes">Bar jedno kompletno slaganje </option>
      <option value="partial">Bar jedan potencijalni put</option>
      <option value="errors">Bar jedna precrtana ulica</option>
      <option value="no">Bez potencijalnih puteva</option>
    </select>
</div>

<table id="list" class="table table-sm table-striped table-bordered table-hover w-100">
<thead class="thead-dark sticky-top">
	<tr>
		<th>Id (RGZ)</th>
		<th>Ulica (RGZ)</th>
		<th>Dužina (RGZ)</th>
		<th>Conflated putevi (dužina)</th>
		<th>Conflated - max greška (m)</th>
		<th>Potencijalni putevi (% poklapanja, dužina)</th>
	</tr>
</thead>
<tbody>
    {% for street in streets %}
    <tr>
        <td>{{ street.rgz_ulica_mb }}</td>
        <td><a href="{{ street.rgz_geojson_url }}" target="_blank">{{ street.rgz_ulica }}</a> {% if street.rgz_ulica_proper != '' %} ➝ {{ street.rgz_ulica_proper }}{% endif %} </td>
        <td data-order="{{ street.rgz_way_length }}">{{ street.rgz_way_length }}m</td>
        <td data-order="{{ street.max_conflated_osm_way_length }}">
            {% if street.conflated_ways|length > 0 %}
            <ul>
            {% for conflated_way in street.conflated_ways %}
                <li><a href="{{ conflated_way.osm_link }}" target="_blank">{{ conflated_way.osm_id }}</a> ({{ conflated_way.conflated_osm_way_length }}m)</li>
            {% endfor %}
            </ul>
            {% endif %}
        </td>
        <td data-order="{% if street.conflated_max_error %}{{ street.conflated_max_error }}{% else %}-1{% endif %}">{% if street.conflated_max_error %}{{ street.conflated_max_error }}m{% endif %}</td>
        <td data-order="{{ street.found_max_found_intersection }}">
            {% if street.found_ways|length > 0 %}
            <ul>
            {% for found_way in street.found_ways %}
                <li>
                    <a href="{{ found_way.osm_link }}" target="_blank">
                        {% if found_way.name_match %}
                        ✅
                        {% elif found_way.norm_name_match %}
                        ⚠️
                        {% endif %}
                        {% if found_way.wrong_name %}
                        <s>
                        {% endif %}
                        {{ found_way.osm_name }}
                        {% if found_way.wrong_name %}
                        </s>
                        {% endif %}
                    </a>
                    ({{ found_way.found_intersection }}%, {{ found_way.found_osm_way_length }}m)
                </li>
            {% endfor %}
            </ul>
            {% endif %}
        </td>
    </tr>
    {% endfor %}
</tbody>
</table>


{% endblock %}