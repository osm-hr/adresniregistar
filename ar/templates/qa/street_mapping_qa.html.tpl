{% extends "base.html" %}
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
			<li><b>RGZ ulica</b> &mdash; Ime ulice u RGZ-u</li>
			<li><b>Ispravan naziv</b> &mdash; Kako DINA platforma misli da treba da bude pravilno ime ulice</li>
			<li><b>Izvor</b> &mdash; Odakle DINA platforma misli da je ovo pravilno ime ulice.
			Može biti: „ručno provereno” (ljudi su ručno gledali kroz tabelu i proveravali), „OSM” (neko je koristio već ovo ime u OSM-u),
			„ref:RS:ulica” (neka ulica je povezana sa registrom i nosi ovo ime) i „Algoritam” (nikako drugačije ulica nije nađena, pa je algoritam heuristikom pokušao da nađe najbolje ime za ulicu)</li>
			<li><b>Reference</b> &mdash; Ukoliko je ime uzeto iz OSM-a ili preko ref:RS:ulica taga, ovde su navedene neke reference (ukoliko ih ima više od 5, samo prvih 5 su navedene)</li>
			<li><b>Izuzeci po opštinama</b> &mdash; Ukoliko u nekoj opštini standardni naziv nije tačan, biće naveden ovde</li>
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
	  <li class="breadcrumb-item" aria-current="page"><a href="qa.html">QA</a></li>
	  <li class="breadcrumb-item" aria-current="page">Nazivi ulica</li>
  </ol>
</nav>
    <!-- Optional JavaScript -->
    <!-- jQuery first, then Popper.js, then Bootstrap JS -->
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>
    <script src="https://cdn.datatables.net/1.10.18/js/jquery.dataTables.min.js" crossorigin="anonymous"></script>
    <script src="https://cdn.datatables.net/1.10.18/js/dataTables.bootstrap4.min.js" crossorigin="anonymous"></script>

<h2>Ispravni nazivi ulica</h2>
<br/>
<p>Pošto su nazivi ulica u RGZ-u napisani velikim slovima, koristi se ova tabela da pretvori nazive iz RGZ-a u nazive kakve treba imati u OSM-u.
    <br/>
    Na osnovu ovih naziva se generišu imena ulica za uvoz adresa, kao i detektuju sve greške u QA analizama.
    <br/>
    Kako smo došli do baš ovakvih naziva možete pogledati na <a href="https://community.openstreetmap.org/t/pravilno-imenovanje-ulica/96891">temi na forumu</a>.
    Ukoliko primetite neku grešku, molimo Vas da prijavite grešku <a href="https://gitlab.com/osm-serbia/adresniregistar/-/issues/new">ovde</a> (potrebno je prvo se registrovati), ili ostavite komentar na istoj
    <a href="https://community.openstreetmap.org/t/pravilno-imenovanje-ulica/96891">temi na forumu</a>,
    a možete poslati izmenu <a href="https://gitlab.com/osm-serbia/adresniregistar/-/blob/main/ar/curated_streets.csv?ref_type=heads">direktno kao PR</a>, ako Vam je to lakše.
    Ukoliko se, pak ne slažete sa nekim ispravkama, najbolje je da koristite forum (ukoliko imate i on-the-ground informaciju kao npr. sliku sa tablom adrese - tim bolje!).
    <br/>
    Zbog velike količine podataka (36.000 adresa u RGZ-u), ova tabela nema napredne funkcije pretrage i sortiranja (pošto bi strana bi bila prespora).
    Stoga je sortiranje ispod već urađeno, i to po azbučnom redu, a za pretragu koristite Ctrl+F mogućnosti browser-a.
</p>
<br/>
<br/>

<table id="list" class="table table-sm table-striped table-bordered table-hover w-75">
<thead class="thead-dark sticky-top">
	<tr>
        <th>RGZ ulica</th>
		<th>Ispravan naziv</th>
		<th>Izvor</th>
		<th>Reference</th>
		<th>Izuzeci po opštinama</th>
	</tr>
</thead>
<tbody>
	{% for street_name in street_names %}
	<tr>
        <td>{{ street_name.rgz_name }}</td>
        <td>{{ street_name.name }}</td>
        <td>
        {% if street_name.source == 'curated' %}
            Ručno provereno
        {% elif street_name.source == 'BestEffort' %}
            Algoritam
        {% elif street_name.source == 'OSM' %}
            OSM
        {% elif street_name.source == 'ref:RS:ulica' %}
            ref:RS:ulica
        {% else %}
            Nepoznat
        {% endif %}
        </td>
        <td>
            <ul>
            {% for r in street_name.refs %}
                <li><a href="{{ r.osm_link }}" target="_blank">{{ r.osm_id }}</a></li>
            {% endfor %}
            </ul>
            {% if street_name.refs_count > 5 %}
                ... još {{ street_name.refs_count }} referenci
            {% endif %}
        </td>
        <td>
            <ul>
            {% for exc in street_name.exceptions %}
                <li>{{ exc.opstina }}: {{ exc.name }}</li>
            {% endfor %}
            </ul>
        </td>
	</tr>
	{% endfor %}
</tbody>
</table>

{% endblock %}

