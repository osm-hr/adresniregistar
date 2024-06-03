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
			<li><b>Opština</b> &mdash; Opština analize</li>
			<li><b># Pogrešan „int_name”</b> &mdash; Ukupan broj adresa gde se „int_name” tag i „name” tag ne slažu. Ne znači da je „int_name” pogrešan, možda je i „name” tag pogrešan!</li>
			<li><b># Nedostaje „int_name”</b> &mdash; Ukupan broj adresa gde „int_name” tag ne postoji.</li>
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
	<li class="breadcrumb-item" aria-current="page"><a href="qa.html">QA</a></li>
	<li class="breadcrumb-item" aria-current="page">Int nazivi</li>
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
		        { targets: [1], className: 'text-right' },
		    ]
		});
	} );
    </script>

<h2>Int nazivi ulica</h2>
<br/>
<p>Ovde možete da vidite potencijalne probleme sa „int_name” tagom za ulice u OpenStreetMap-apa. Moguće je da „int_name” tag fali, a moguće je i da je pogrešan.
    Klikom na opštinu dobijate detaljnije podatke za tu opštinu. U gornjem desnom uglu je filtriranje.
    <br/>
    <br/>
    Da biste bolje razumeli značenje kolona u tabeli, pogledajte <a href="" data-toggle="modal" data-target="#exampleModal">„Pomoć”</a>.
    <br/>
    <br/>
    <b>Pažljivo prilikom otvaranja opština preko 5.000 adresa, računar i browser mogu da se uspore znatno!</b>
</p>
<br/>
<br/>

<table id="list" class="table table-sm table-striped table-bordered table-hover w-50">
<thead class="thead-dark sticky-top">
	<tr>
		<th>Opština</th>
		<th># Pogrešan „int_name”</th>
		<th># Nedostaje „int_name”</th>
	</tr>
</thead>
<tbody>
	{% for opstina in opstine %}
	<tr>
		<td><a href="int_names/{{ opstina.name }}.html">{{ opstina.name }}</a></td>
		<td>{{ opstina.wrong_int_name }}</td>
		<td>{{ opstina.missing_int_name }}</td>
	</tr>
	{% endfor %}
</tbody>
<tfoot>
	<tr>
		<th>Serbia TOTAL:</th>
		<th class="d-sm-table-cell">{{ total.wrong_int_name }}</th>
		<th class="d-sm-table-cell">{{ total.missing_int_name }}</th>
	</tr>
</tfoot>
</table>

{% endblock %}