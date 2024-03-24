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
		  Ovde su izlistane sve adrese iz OSM-a kojima je "ref:RS:kucni_broj" dupliciran, tj. više OSM adresa deli istu referencu ka RGZ adresi.
		  <br/>
		  Ovo ne sme da se dešava i verovatno je samo jedna adresa iz OSM-a "prava", tj. dobra dok su ostale greška.
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
	<li class="breadcrumb-item active" aria-current="page">ref:RS:kucni_broj duplikati</li>
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
		lengthMenu: [ [10, 50, -1], [10, 50, "All"] ],
		columnDefs: [
		]
	});
} );
</script>


{% if len(duplicates) > 0 %}
<table id="list" class="table table-sm table-striped table-bordered table-hover w-50">
<thead class="thead-dark sticky-top">
	<tr>
		<th>ref:RS:kucni_broj</th>
		<th>Opština</th>
		<th>Duplikati</th>
	</tr>
</thead>
<tbody>
	{% for duplicate in duplicates %}
	<tr>
		<td>{{ duplicate.id }}</td>
		<td>{{ duplicate.opstina }}</td>
		<td>
			{% for link in duplicate.links %}
			<a href="{{ link.href }}" target="_blank">{{ link.name }}</a>
			<br/>
			{% endfor %}
		</td>
	</tr>
	{% endfor %}
</tbody>
</table>
{% endif %}

{% if len(duplicates) == 0 %}
<div class="text-center">
	<h2>Nema duplikata!</h2>
</div>
{% endif %}

{% endblock %}
