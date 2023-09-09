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
			<li><b>Opština</b> &mdash; Opština sa stambenim zajednicama</li>
			<li><b>Broj stambenih zajednica</b> &mdash; Ukupan broj stambenih zajednica u registru</li>
			<li><b>Pronađeno u AR-u</b> &mdash; Broj pronađenih stambenih zajednica u adresnom registru na osnovu opštine, ulice i kućnog broja</li>
			<li><b>Pronađeno u AR-u [%]</b> &mdash; Broj pronađenih stambenih zajednica u adresnom registru na osnovu opštine, ulice i kućnog broja</li>
			<li><b>Pronađeno u OSM-u</b> &mdash; Broj pronađenih stambenih zajednica na osnovu <code>ref:RS:kucni_broj</code> taga u OSM-u</li>
			<li><b>Pronađeno u OSM-u [%]</b> &mdash; Procenat pronađenih stambenih zajednica (u odnosu na one nađene u adresnom registru) na osnovu <code>ref:RS:kucni_broj</code> taga u OSM-u</li>
			<li><b>Apartments</b> &mdash; Broj onih stambenih zajednica nađenih u OSM-u koje su pravilno tagovane kao <code>building=apartments</code> u OSM-u</li>
			<li><b>Apartments [%]</b> &mdash; Procenat onih stambenih zajednica nađenih u OSM-u (u odnosu na sve nađene u OSM-u) koje su pravilno tagovane kao <code>building=apartments</code> u OSM-u</li>
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
	  <li class="breadcrumb-item" aria-current="page">Početna</li>
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
	    $('#list').DataTable({
		    stateSave: true,
		    order: [[0, 'asc']],
		    columnDefs: [
		        { targets: [1,2,3,4,5,6,7], className: 'text-right' },
		    ]
		});
		$('#list_resolution').DataTable({
		    stateSave: true,
		    order: [[1, 'desc']]
		});
	} );
    </script>

<h2>Analiza stambenih zajednica</h2>
<br/>

<p>Ovde je spisak svih stambenih zajednica iz RGZ-a. Ovo nam pomaže da sve zgrade koje se vode kao stambene zajednice
tagujemo u OSM-u kao <code>building=apartments</code>. Pročitajte na dnu kako su ovi podaci izgenerisani i kako da ih tumačite.
    Klikom na opštinu dobijate podatke za tu opštinu. U gornjem desnom uglu je filtriranje.
    U gornjem desnom uglu je filtriranje. Klikom na "Pomoć" u gornjem meniju dobićete više informacija o kolonama u ovoj tabeli.
</p>
<br/>
<br/>

<table id="list" class="table table-sm table-striped table-bordered table-hover w-100">
<thead class="thead-dark sticky-top">
	<tr>
		<th>Opština</th>
		<th>Broj stambenih zajednica</th>
		<th>Pronađeno u AR-u</th>
		<th>Pronađeno u AR-u [%]</th>
		<th>Pronađeno u OSM-u</th>
		<th>Pronađeno u OSM-u [%]</th>
		<th>Apartments</th>
		<th>Apartments [%]</th>
	</tr>
</thead>
<tbody>
	{% for opstina in opstine %}
	<tr>
		<td><a href="{{ opstina.name }}.html">{{ opstina.name }}</a></td>
		<td>{{ opstina.sz_count }}</td>
		<td>{{ opstina.found_in_rgz }}</td>
		<td data-order="{% if opstina.sz_count > 0 %}{{ (100 * opstina.found_in_rgz) / opstina.sz_count }}{% else %}-1{% endif %}">
            {% if opstina.sz_count > 0 %}
            {{ '{0:0.2f}'.format((100.0 * opstina.found_in_rgz) / opstina.sz_count) }}%
            {% else %}
            /
            {% endif %}
		</td>
		<td>{{ opstina.found_in_osm }}</td>
		<td data-order="{% if opstina.found_in_rgz > 0 %}{{ (100 * opstina.found_in_osm) / opstina.found_in_rgz }}{% else %}-1{% endif %}">
            {% if opstina.found_in_rgz > 0 %}
            {{ '{0:0.2f}'.format((100.0 * opstina.found_in_osm) / opstina.found_in_rgz) }}%
            {% else %}
            /
            {% endif %}
		</td>
		<td>{{ opstina.apartments_count }}</td>
		<td data-order="{% if opstina.found_in_osm > 0 %}{{ (100 * opstina.apartments_count) / opstina.found_in_osm }}{% else %}-1{% endif %}">
            {% if opstina.found_in_osm > 0 %}
            {{ '{0:0.2f}'.format((100.0 * opstina.apartments_count) / opstina.found_in_osm) }}%
            {% else %}
            /
            {% endif %}
		</td>
	</tr>
	{% endfor %}
</tbody>
<tfoot>
	<tr>
		<th>Serbia TOTAL:</th>
		<th class="d-sm-table-cell">{{ total.sz_count }}</th>
		<th class="d-sm-table-cell">{{ total.found_in_rgz }}</th>
		<th class="d-sm-table-cell">{{ '{0:0.2f}'.format((100.0 * total.found_in_rgz) / total.sz_count) }}%</th>
		<th class="d-sm-table-cell">{{ total.found_in_osm }}</th>
		<th class="d-sm-table-cell">{{ '{0:0.2f}'.format((100.0 * total.found_in_osm) / total.found_in_rgz) }}%</th>
		<th class="d-sm-table-cell">{{ total.apartments_count }}</th>
		<th class="d-sm-table-cell">{{ '{0:0.2f}'.format((100.0 * total.apartments_count) / total.found_in_osm) }}%</th>
	</tr>
</tfoot>
</table>

<div class="row">
    <div id="tester" class="col-md-8 offset-2">
    </div>
</div>

<script>
var gd = document.getElementById('tester');
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
    margin: {l: 250},
    width:600,
    height: 500,
    dragmode: false,
    separators: ',.'}
Plotly.newPlot('tester', data, layout, {displayModeBar: false});
</script>

<hr/>
<br/>
<p>RGZ, nažalost, u spisku stambenih zajednica daje samo opštinu, ulicu i broj. Ne daje identifikator adrese iz adresnom registra,
ne daje geografsku širinu i visinu adrese, a često se ni imena ulica iz registra stambenih zajednica i adresnog registra ne slažu!
Zbog ovoga je proces spajanja ovih adresa otežan i ovde je pokušano da se spoji što se više moglo, ali ne treba očekivati 100% poklapanja.
<br/>
<br/>
Prvo se, na osnovu opštine, ulice i kućnog broja, proba da nađe takva adresa u adresnom registru RGZ-a. Ako se to ne uspe (obično jer se ulice
razlikuju), odustajemo. Sve što je pronađeno se vidi kao pronađeno u koloni <b>„Pronađeno u AR-u”.</b>. Time smo dobili identifikator
stambene zajednice iz adresnog registra.
<br/>
<br/>
Sledeći korak je pronalaženje tog identifikatora unutar OSM-a na osnovu
<a href="https://openstreetmap.rs/download/ar/index.html" target="_blank">uvoza RGZ adresa</a>. Ukoliko se adresa ne pronađe, odustajemo i čekamo
da bude uneta u uvozu. Ako je pronađena, videćemo je u koloni <b>„Pronađeno u OSM-u”.</b>. Time smo dobili OSM entitet.
<br/>
<br/>
Kada imamo OSM entitet, možemo da vidimo da li je on čvor, linija ili relacija, da li je tagovan kao <code>building</code> i
da li je vrednost tog taga <code>apartments</code>. Idealan slučaj koji nam treba je da je adresa ili linija koja je tagovana
kao <code>building=apartments</code> ili da je adresa čvor koji je zakačen za liniju koja je tagovana kao <code>building=apartments</code>.
<br/>
<br/>
Ostale opštine iz Srbije koje nisu navedene nemaju nijednu stambenu zajednicu na spisku.

</p>

{% endblock %}

