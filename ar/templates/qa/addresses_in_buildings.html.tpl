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
			<li><b>Opština</b> &mdash; Opština analize</li>
			<li><b>#</b> &mdash; Ukupan broj adresa unutar zgrada</li>
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
	<li class="breadcrumb-item" aria-current="page"><a href="index.html">Adrese</a></li>
	<li class="breadcrumb-item" aria-current="page"><a href="qa.html">QA</a></li>
	<li class="breadcrumb-item" aria-current="page">Adrese unutar zgrada</li>
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
		    stateDuration: 0,
		    order: [[0, 'asc']],
		    lengthMenu: [ [10, 50, -1], [10, 50, "All"] ],
		    columnDefs: [
		        //{ targets: [10, 11, 12, 13, 14], "orderable": false},
		        //{ targets: [1], visible: false },
		        { targets: [1], className: 'text-right' },
		        //{ targets: '_all', visible: false }
		    ]
		});
		$('#list_resolution').DataTable({
		    stateSave: true,
		    order: [[1, 'desc']]
		});
	} );
    </script>

<h2>Adrese unutar zgrada po opštinama</h2>
<br/>
<p>Ovde možete videti ukupan broj adresa koje se nalaze unutar zgrada, po opštinama.
    Klikom na opštinu dobijate podatke za tu opštinu. U gornjem desnom uglu je filtriranje. Ispod ove tabele se nalaze statistike po kategorijama. Više o kategorijama možete videti tamo.
    <br/>
    <b>Pažljivo prilikom otvaranja opština preko 5.000 adresa, računar i browser mogu da se uspore znatno!</b>
</p>
<br/>
<br/>

<table id="list" class="table table-sm table-striped table-bordered table-hover w-25">
<thead class="thead-dark sticky-top">
	<tr>
		<th>Opština</th>
		<th>#</th>
	</tr>
</thead>
<tbody>
	{% for opstina in opstine %}
	<tr>
		<td><a href="qa_addresses/{{ opstina.name }}.html">{{ opstina.name }}</a></td>
		<td>{{ opstina.count }}</td>
	</tr>
	{% endfor %}
</tbody>
<tfoot>
	<tr>
		<th>Serbia TOTAL:</th>
		<th class="d-sm-table-cell">{{ total.count }}</th>
	</tr>
</tfoot>
</table>

<br/>
<br/>
<br/>
<hr/>

<h2>Broj različitih kategorija</h2>
<br/>
<p>Ovde možete videti ukupan broj adresa koje se nalaze unutar zgrada, po kategorijama. Neke od kategorija se mogu rešiti automatizacijom, ali većina zahteva ljudsku pažnju.</p>
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
            Nešto nije u redu, ali postoji "note" tag na zgradi, adresi ili POI-u i ništa se ne automatizuje
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

