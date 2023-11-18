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
            Izveštaj je još u fazi izrade. Trenutno nalazi više stvari nego što treba, tako da ga uzmite sa rezervom.
            <ul>
                <li><b>Zgrada</b> &mdash; OSM zgrada unutar koje su nađene adrese</li>
                <li><b>Zgradina adresa</b> &mdash; Ukoliko na zgradi ima addr:street i addr:housenumber, ovde će biti prikazani</li>
                <li><b>Zgrada ima ref:RS:kucni_broj</b> &mdash; Da li na zgradi postoji dodeljen ref:RS:kucni_broj tag</li>
                <li><b>Broj adresa</b> &mdash; Ukupan broj pronađenih adresa unutar zgrade</li>
                <li><b>Adresa(e)</b> &mdash; OSM adresa unutar zgrade</li>
                <li><b>Adresa(e) imaju ref:RS:kucni_broj</b> &mdash; Da li na adresama unutar zgrade postoji dodeljen ref:RS:kucni_broj tag</li>
                <li><b>Kategorija</b> &mdash; Opisuje kategorizaciju, tj. koji je slučaj u pitanju i kako eventualno može da se reši</li>
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
	  <li class="breadcrumb-item" aria-current="page"><a href="../index.html">Početna</a></li>
	  <li class="breadcrumb-item" aria-current="page"><a href="../qa.html">QA</a></li>
      <li class="breadcrumb-item" aria-current="page"><a href="../addresses_in_buildings.html">Adrese unutar zgrada</a></li>
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
	    $('#list').DataTable({
		    stateSave: true,
		    order: [[0, 'desc']],
		    lengthMenu: [ [10, 100, -1], [10, 50, "All"] ],
		    columnDefs: [
		        //{ targets: [10, 11, 12, 13, 14], "orderable": false},
		        //{ targets: [1], visible: false },
		        { targets: [2, 5], className: 'text-right' },
		        //{ targets: '_all', visible: false }
		    ]
		});
		$('#list_resolution').DataTable({
		    stateSave: true,
		    order: [[1, 'desc']]
		});
	} );
    </script>

<h2>Adrese unutar zgrade za "{{ opstina_name }}"</h2>
<br/>
<p>Ovde možete videti sve zgrade sa svim adresama unutar njihovih poligona, kao i pokušaj njihove kategorizacije.
    Neke od ovih kategorija se mogu rešiti automatizacijim.
    {% if len(osm_files_move_address_to_building) > 0 %}
    U dnu se nalazi spisak fajlova.
    {% endif %}
    U gornjem desnom uglu je filtriranje. Klikom na <a href="" data-toggle="modal" data-target="#exampleModal">„Pomoć”</a> u gornjem meniju dobićete više informacija o kolonama u ovoj tabeli.
    </p>
<br/>
<br/>


<table id="list" class="table table-sm table-striped table-bordered table-hover w-75">
<thead class="thead-dark sticky-top">
	<tr>
		<th>Zgrada</th>
        <th>Zgradina adresa</th>
		<th>Zgrada ima ref:RS:kucni_broj</th>
        <th>Broj adresa</th>
        <th>Adresa(e)</th>
        <th>Adresa(e) ima ref:RS:kucni_broj</th>
        <th>Kategorija</th>
	</tr>
</thead>
<tbody>
	{% for address in addresses %}
	<tr>
		<td><a href="{{ address.building_osm_link }}" target="_blank">{{ address.building_text }}</a></td>
        <td>{{ address.building_address}}</td>
		<td>{% if addresses.building_has_ref %}✅{% else %}❌{% endif %}</td>
        <td>{{ len(address.nodes) }}</td>
        <td>
            <ul>
            {% for node in address.nodes %}
                <li><a href="{{ node.link }}" target="_blank">{{ node.text }}</a></li>
            {% endfor %}
            </ul>
        </td>
        <td>
        {% for node in address.nodes %}
            {% if node.has_ref %}✅{% else %}❌{% endif %}
            <br/>
        {% endfor %}
        </td>
        <td>
            {% if address.resolution == AddressInBuildingResolution.NO_ACTION %}
            Sve kako treba!
            {% elif address.resolution == AddressInBuildingResolution.MERGE_POI_TO_BUILDING %}
            POI bi mogao da se premesti na zgradu (ukoliko je namena zgrade ista)
            {% elif address.resolution == AddressInBuildingResolution.MERGE_ADDRESS_TO_BUILDING %}
            Adresa unutar zgrade treba da se premesti na zgradu. Pogledajte fajlove iznad za ovo.
            {% elif address.resolution == AddressInBuildingResolution.COPY_POI_ADDRESS_TO_BUILDING %}
            Adresa POI-a može da se prekopira i na zgradu.
            {% elif address.resolution == AddressInBuildingResolution.ATTACH_ADDRESSES_TO_BUILDING %}
            Zakačiti čvorove adrese(a) na zgradu
            {% elif address.resolution == AddressInBuildingResolution.REMOVE_ADDRESS_FROM_BUILDING %}
            Uklonite adresu sa zgrade, već je adresa na tačkama unutar zgrade
            {% elif address.resolution == AddressInBuildingResolution.ADDRESSES_NOT_MATCHING %}
            Adrese unutar zgrade i na zgradi se ne poklapaju, razrešite ručno
            {% elif address.resolution == AddressInBuildingResolution.CASE_TOO_COMPLEX %}
            Mešavina POI-a i adresa unutar zgrade, razrešite ručno
            {% elif resolution == AddressInBuildingResolution.BUILDING_IS_NODE %}
            Ova zgrada je zapravo čvor sa tagom "building", treba izbrisati "building" tag
            {% elif resolution == AddressInBuildingResolution.NOTE_PRESENT %}
            Nešto nije u redu, ali postoji "note" tag na zgradi, adresi ili POI-u i ništa se ne automatizuje
            {% else %}
            Kategorija nepoznata
            {% endif %}
        </td>
	</tr>
	{% endfor %}
</tbody>
</table>

{% if len(osm_files_move_address_to_building) > 0 %}
<h2>Lista fajlova za import</h2>

<div class="row">
	<div class="col-sm">
	  <a class="btn btn-primary" data-toggle="collapse" href="#collapseOsmFilesNew" role="button" aria-expanded="false" aria-controls="collapseOsmFilesNew">
		Kategorija - prebacivanja adrese sa čvora na zgradu!
	  </a>
	</div>
</div>

<div class="collapse" id="collapseOsmFilesNew">
  Ovde su fajlovi za brisanje adresa kao čvorova i prebacivanje svih njihovih tagova na poligon zgrade.
    Morate imati otvoren JOSM pre nego što kliknete na fajl.
	Klikom na fajl ćete ga učitati u JOSM.
	Fajlovi su grupisani u grupe od po najviše 10 adresa.
	<br/>
    <br/>
	<b>Pre bilo kakve automatizacije, <b>obavezno</b> pročitati <a href="https://wiki.openstreetmap.org/wiki/Serbia/Projekti/Adresni_registar#Uputstvo_za_import" target="_blank">uputstvo</a></b>!
    <br/>
  <div class="card card-body">
	  <div class="row row-cols-5">
	  	{% for osm_file in osm_files_move_address_to_building %}
	  		<div class="col-sm">
	  			<a href="http://localhost:8111/import?changeset_tags=source=RGZ_AR&new_layer=true&layer_name={{ osm_file.name }}&url={{ osm_file.url }}" target="_blank">{{ osm_file.name }}</a>
			</div>
	  	{% endfor %}
	  </div>
  </div>
</div>
<br/><br/>
{% endif %}

<br/>
<br/>
<br/>
<hr/>

<h2>Broj različitih kategorija</h2>
<br/>
<p>Ovde možete videti ukupan broj adresa koje se nalaze unutar zgrada, po kategorijama unutar opštine „{{ opstina_name }}”.
    Neke od kategorija se mogu rešiti automatizacijom, ali većina zahteva ljudsku pažnju.</p>
<br/>
<br/>

<table id="list_resolution" class="table table-sm table-striped table-bordered table-hover w-25">
<thead class="thead-dark sticky-top">
	<tr>
		<th>Kategorija</th>
        <th>Broj pojavljivanja</th>
	</tr>
</thead>
<tbody>
	{% for resolution, count in resolution_stats.items() %}
    {% if resolution == AddressInBuildingResolution.NO_ACTION %}
    {% else %}
	<tr>
        <td>
            {% if resolution == AddressInBuildingResolution.NO_ACTION %}
            Sve kako treba!
            {% elif resolution == AddressInBuildingResolution.MERGE_POI_TO_BUILDING %}
            POI bi mogao da se premesti na zgradu (ukoliko je namena zgrade ista)
            {% elif resolution == AddressInBuildingResolution.MERGE_ADDRESS_TO_BUILDING %}
            Adresa unutar zgrade treba da se premesti na zgradu. Pogledajte fajlove iznad za ovo.
            {% elif resolution == AddressInBuildingResolution.COPY_POI_ADDRESS_TO_BUILDING %}
            Adresa POI-a može da se prekopira i na zgradu.
            {% elif resolution == AddressInBuildingResolution.ATTACH_ADDRESSES_TO_BUILDING %}
            Zakačiti čvorove adrese(a) na zgradu
            {% elif resolution == AddressInBuildingResolution.REMOVE_ADDRESS_FROM_BUILDING %}
            Uklonite adresu sa zgrade, već je adresa na tačkama unutar zgrade
            {% elif resolution == AddressInBuildingResolution.ADDRESSES_NOT_MATCHING %}
            Adrese unutar zgrade i na zgradi se ne poklapaju, razrešite ručno
            {% elif resolution == AddressInBuildingResolution.CASE_TOO_COMPLEX %}
            Mešavina POI-a i adresa unutar zgrade, razrešite ručno
            {% elif resolution == AddressInBuildingResolution.BUILDING_IS_NODE %}
            Ova zgrada je zapravo čvor sa tagom „building”, treba izbrisati „building” tag
            {% elif resolution == AddressInBuildingResolution.NOTE_PRESENT %}
            Nešto nije u redu, ali postoji „note” tag na zgradi, adresi ili POI-u i ništa se ne automatizuje
            {% else %}
            Kategorija nepoznata
            {% endif %}
        </td>
        <td>{{ count }}</td>
	</tr>
    {% endif %}
	{% endfor %}
</tbody>
</table>

{% endblock %}

