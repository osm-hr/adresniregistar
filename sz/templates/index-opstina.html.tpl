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
			<li><b>Ime (SZ)</b> &mdash; Ime kako je navedeno u registru stambenih zajednica</li>
			<li><b>Ulica i kućni broj (SZ)</b> &mdash; Ime ulice i kućni broj u registru stambenih zajednica</li>
			<li><b>Nađen u AR-u</b> &mdash; Ako je stambena zajednica nađena u adresnom registru, ovde će biti ✅ i ulica i kućni broj, kao i identifikator kako stoje u AR-u.
			Ako nije nađeno, stajaće ❌. Ako nema ništa dodatno upisano, takva ulica i kućni broj ne postoje u AR-u. Ako piše "dup", tu su
			navedena naselja koja imaju istu ulicu i broj i zbog te dvosmislenosti se ne zna za koje naselje se ulica odnosi</li>
			<li><b>Nađen u OSM-u</b> &mdash; Ako je stambena zajednica sa identifikatorom iz AR-a nađena u OSM-u preko <code>ref:RS:kucni_broj</code> taga,
			ovde će biti ulica i broj iz OSM-a i link ka OSM entitetu</li>
			<li><b>Stanje u OSM-u</b> &mdash; U idealnom slučaju, čvor iz OSM-a će biti zakačen na zgradu tagovanu kao <code>building=apartments</code> ili će adresa
			već biti na zgradi ili relaciji koja je ovako tagovana. Ukoliko to nije slučaj iz nekog razloga, ovde će biti upisano stanje.</li>
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
	  <li class="breadcrumb-item" aria-current="page"><a href="index.html">Početna</a></li>
	  <li class="breadcrumb-item" aria-current="page">{{ opstina_name }}</li>
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
			let arState = $("#foundInAR option:selected").val();
			let osmState = $("#foundInOSM option:selected").val();

            let arStateFilter = true;
            if (arState === 'yes') {
                arStateFilter = data[2].indexOf('✅') > -1;
            } else if (arState === 'no_notfound') {
                arStateFilter = data[2].indexOf('❌') > -1 && data[2].indexOf('dup') === -1;
            } else if (arState === 'no_dup') {
                arStateFilter = data[2].indexOf('❌') > -1 && data[2].indexOf('dup') > -1;
            } else if (arState === 'no') {
                arStateFilter = data[2].indexOf('❌') > -1;
            }

			let osmStateFilter = true;
			if (osmState === 'yes') {
			    osmStateFilter = data[3].indexOf('✅') > -1;
			} else if (osmState === 'yes_nodedetached') {
			    osmStateFilter = data[3].indexOf('✅') > -1 && data[4].indexOf('Čvor') > -1;
			} else if (osmState === 'yes_notbuilding') {
                osmStateFilter = data[3].indexOf('✅') > -1 && data[4].indexOf('zgrada') > -1;
			} else if (osmState === 'yes_notapartments') {
			    osmStateFilter = data[3].indexOf('✅') > -1 && data[4].indexOf('apartments') > -1;
			} else if (osmState === 'yes_apartments') {
			    osmStateFilter = data[3].indexOf('✅') > -1 && data[4].indexOf('✅') > -1;
			} else if (osmState === 'no') {
			     osmStateFilter = data[3].indexOf('❌') > -1;
			}

			return arStateFilter && osmStateFilter;
		});

	    var table = $('#list').DataTable({
		    stateSave: true,
		    order: [[0, 'asc']],
		    columnDefs: [
		        { targets: [3], className: 'text-right' },
		    ]
		});

        $('#foundInAR').on('change', function() {
            table.draw();
        });
        $('#foundInOSM').on('change', function() {
            table.draw();
        });

	} );
    </script>

<h2>Analiza stambenih zajednica za opštinu „{{ opstina_name }}”</h2>
<br/>

<p>Ovde je spisak svih stambenih zajednica iz RGZ-a za opštinu „{{ opstina_name }}”.
<br/>
U gornjem desnom uglu je filtriranje.
Klikom na "Pomoć" u gornjem meniju dobićete više informacija o kolonama u ovoj tabeli. Ispod tabele se nalaze dodatni grafici.
</p>
<br/>
<br/>

<div class="text-right">
    <label for="arState">AR stanje:</label>
    <select name="arState" id="foundInAR">
      <option value="all"></option>
      <option value="yes">Nađeno</option>
      <option value="no">Nije nađeno</option>
      <option value="no_notfound">&nbsp;&nbsp; Ulica i broj nisu nađeni u opštini</option>
      <option value="no_dup">&nbsp;&nbsp; Više naselja sa istom ulicom i brojem</option>
    </select>

    <br/>

    <label for="osmState">OSM stanje:</label>
    <select name="osmState" id="foundInOSM">
      <option value="all"></option>
      <option value="yes">Nađeno</option>
      <option value="yes_nodedetached">&nbsp;&nbsp; Čvor van zgrade</option>
      <option value="yes_notbuilding">&nbsp;&nbsp; Nije tagovana kao zgrada</option>
      <option value="yes_notapartments">&nbsp;&nbsp; Nije tagovana kao building=apartments</option>
      <option value="yes_apartments">&nbsp;&nbsp; Tagovana kao building=apartment</option>
      <option value="no">Nije nađeno</option>
</select>
</div>

<table id="list" class="table table-sm table-striped table-bordered table-hover w-100">
<thead class="thead-dark sticky-top">
	<tr>
		<th>Ime (SZ)</th>
		<th>Ulica i kućni broj (SZ)</th>
		<th>Nađen u AR-u</th>
		<th>Nađen u OSM-u</th>
		<th>Stanje u OSM-u</th>
	</tr>
</thead>
<tbody>
	{% for address in addresses %}
	<tr>
		<td>{{ address.sz_ime }}</td>
		<td>{{ address.sz_ulica }} {{ address.sz_kucni_broj }}</td>
		<td>
		    {% if address.found_in_rgz %}
		        ✅ {{ address.rgz_ulica }} {{ address.rgz_kucni_broj }} (<a href="{{ address.rgz_link }}" target="_blank">{{ address.rgz_kucni_broj_id }}</a>)
		    {% else %}
		    ❌
		    {% if address.duplicated_naselja %}
		        (dup: {{ address.duplicated_naselja }})
		    {% endif %}
		    {% endif %}
		</td>
		<td>
		    {% if address.found_in_osm %}
		        ✅
		        {% for osm_link in address.osm_links %}
		            <a href="{{ osm_link }}" target="_blank">{{ address.osm_streets[loop.index0] }} {{ address.osm_housenumbers[loop.index0] }}</a>{% if loop.index < len(address.osm_links) %},{% endif %}
		        {% endfor %}
		    {% else %}
		    ❌
		    {% endif %}
		</td>
		<td>
		    {% if address.resolution == ApartmentResolution.OSM_ENTITY_NOT_FOUND %}
		    ❌ Grеška u traženju OSM entiteta (verovatno je nedavno dodat ili obrisan)
		    {% elif address.resolution == ApartmentResolution.NODE_DETACHED %}
		    ❌ Čvor van zgrade
		    {% elif address.resolution == ApartmentResolution.OSM_ENTITY_NOT_BUILDING %}
		    ❌ Nije tagovana kao zgrada
		    {% elif address.resolution == ApartmentResolution.OSM_ENTITY_NOT_APARTMENT %}
		    ❌ Nije tagovana kao building=apartments
		    {% elif address.resolution == ApartmentResolution.OSM_ENTITY_APARTMENT %}
		    ✅
		    {% else %}
		    {% endif %}
		</td>
	</tr>
	{% endfor %}
</tbody>
</table>

<div class="row">
    <div id="funnel" class="col-md-8 offset-2">
    </div>
</div>
<div class="row">
    <div id="pie" class="col-md-8 offset-2">
    </div>
</div>

<script>
var gd = document.getElementById('funnel');
var data = [
    {
        type: 'funnel',
        y: ["Broj stambenih zajednica", "Pronađeno u AR-u", "Pronađeno u OSM-u", "Tagovano kao apartments"],
        x: [{{ total.sz_count }}, {{ total.found_in_rgz }}, {{ total.found_in_osm }}, {{ total.apartments_count }}],
        textinfo: "value+percent initial",
        hoverinfo: 'x+percent previous+percent initial',
        texttemplate: '%{value:,d}<br>(%{percentInitial})',
    }
];
var layout = {
    title: 'Funnel stambenih zajednica',
    margin: {l: 150},
    width:600,
    height: 500,
    dragmode: false,
    separators: ',.'}
Plotly.newPlot('funnel', data, layout, {displayModeBar: false});


var data = [{
  values: [
    {{ osm_breakdown[ApartmentResolution.OSM_ENTITY_NOT_FOUND] }},
    {{ osm_breakdown[ApartmentResolution.NODE_DETACHED] }},
    {{ osm_breakdown[ApartmentResolution.OSM_ENTITY_NOT_BUILDING] }},
    {{ osm_breakdown[ApartmentResolution.OSM_ENTITY_NOT_APARTMENT] }},
    {{ osm_breakdown[ApartmentResolution.OSM_ENTITY_APARTMENT] }}
  ],
  labels: ['Nije ni nađeno u OSM-u', 'Čvor nije na zgradi', 'Nije tagovano kao "building"', 'Nije tagovano kao "building=apartments"', 'Sve OK'],
  type: 'pie',
  sort: false
}];

var layout = {
  title: 'Stanje u OSM-u',
  margin: {l: 150},
  height: 500,
  width: 600,
  dragmode: false
};

Plotly.newPlot('pie', data, layout, {displayModeBar: false});
</script>

{% endblock %}
