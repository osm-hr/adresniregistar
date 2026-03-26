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

<table id="list" class="table table-sm table-striped table-bordered table-hover w-75">
<thead class="thead-dark sticky-top">
	<tr>
		<th>Opština</th>
		<th>Ukupno</th>
		<th>Adresa u zgradi</th>
		<th>Više adresa u zgradi</th>
		<th>Neslaganje adresa</th>
		<th>POI u zgradi</th>
		<th>POI i adresa(e) u zgradi</th>
		<th>Nepotrebna adresa</th>
		<th>Beleška</th>
		<th>Adresa POI na zgradu</th>
		<th>Zgrada je čvor</th>
	</tr>
</thead>
<tbody>
	{% for opstina in opstine %}
	<tr>
		<td><a href="qa_addresses/{{ opstina.name }}.html">{{ opstina.name }}</a></td>
		<td>{{ opstina.count }}</td>
		<td>{{ opstina.count_matb }}</td>
		<td>{{ opstina.count_aatb }}</td>
		<td>{{ opstina.count_anm }}</td>
		<td>{{ opstina.count_mptb }}</td>
		<td>{{ opstina.count_ctc }}</td>
		<td>{{ opstina.count_rafb }}</td>
		<td>{{ opstina.count_np }}</td>
		<td>{{ opstina.count_cpatb }}</td>
		<td>{{ opstina.count_bin }}</td>
	</tr>
	{% endfor %}
</tbody>
<tfoot>
	<tr>
		<th>Serbia TOTAL:</th>
		<th class="d-sm-table-cell">{{ total.count }}</th>
		<th class="d-sm-table-cell">{{ total.count_matb }}</th>
		<th class="d-sm-table-cell">{{ total.count_aatb }}</th>
		<th class="d-sm-table-cell">{{ total.count_anm }}</th>
		<th class="d-sm-table-cell">{{ total.count_mptb }}</th>
		<th class="d-sm-table-cell">{{ total.count_ctc }}</th>
		<th class="d-sm-table-cell">{{ total.count_rafb }}</th>
		<th class="d-sm-table-cell">{{ total.count_np }}</th>
		<th class="d-sm-table-cell">{{ total.count_cpatb }}</th>
		<th class="d-sm-table-cell">{{ total.count_bin }}</th>
	</tr>
</tfoot>
</table>

<br/>
<br/>
<br/>
<h3>Objašnjenje kolona</h3>
<ul>
    <li>Adresa u zgradi &mdash; Adresa unutar zgrade treba da se premesti na zgradu. Pogledajte fajlove u pojedinačnim opštinama za ovo.</li>
    <li>Više adresa u zgradi &mdash; Zakačiti čvorove adrese(a) na zgradu.</li>
    <li>Neslaganje adresa &mdash; Adrese unutar zgrade i na zgradi se ne poklapaju, razrešite ručno.</li>
    <li>POI u zgradi &mdash; POI bi mogao da se premesti na zgradu (ukoliko je namena zgrade ista)</li>
    <li>POI i adresa(e) u zgradi &mdash; Mešavina POI-a i adresa unutar zgrade, razrešite ručno.</li>
    <li>Nepotrebna adresa &mdash; Uklonite adresu sa zgrade, već je adresa na tačkama unutar zgrade.</li>
    <li>Beleška &mdash; Nešto nije u redu, ali postoji "note" tag na zgradi, adresi ili POI-u i ništa se ne automatizuje</li>
    <li>Adresa POI na zgradu &mdash; Adresa POI-a može da se prekopira i na zgradu.</li>
    <li>Zgrada je čvor &mdash; Ova zgrada je zapravo čvor sa tagom „building”, treba izbrisati „building” tag</li>
</ul>

{% endblock %}

