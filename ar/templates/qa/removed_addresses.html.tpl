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
			<li><b># „removed:ref:RS:kucni_broj”</b> &mdash; Ukupan broj obrisanih adresa sa „removed:ref:RS:kucni_broj” oznakama</li>
			<li><b># „ref:RS:kucni_broj”</b> &mdash; Ukupan broj obrisanih adresa koje imaju i „removed:ref:RS:kucni_broj” i „ref:RS:kucni_broj” oznaku</li>
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
	<li class="breadcrumb-item" aria-current="page">Obrisane RGZ adrese</li>
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
	} );
    </script>

<h2>Obrisane RGZ adrese</h2>
<br/>
<p>Ovde možete videti sve RGZ adrese koje smo uneli u OSM, ali su one od tad izbrisane iz RGZ-a, po opštinama.
    Klikom na opštinu dobijate podatke za tu opštinu. U gornjem desnom uglu je filtriranje.
</p>
<br/>
<br/>

<table id="list" class="table table-sm table-striped table-bordered table-hover w-25">
<thead class="thead-dark sticky-top">
	<tr>
		<th>Opština</th>
		<th># „removed:ref:RS:kucni_broj”</th>
		<th># „ref:RS:kucni_broj”</th>
	</tr>
</thead>
<tbody>
	{% for opstina in opstine %}
	<tr>
		<td><a href="removed_addresses/{{ opstina.name }}.html">{{ opstina.name }}</a></td>
		<td>{{ opstina.removed_count }}</td>
		<td>{{ opstina.current_count }}</td>
	</tr>
	{% endfor %}
</tbody>
<tfoot>
	<tr>
		<th>Serbia TOTAL:</th>
		<th class="d-sm-table-cell">{{ total.removed_count }}</th>
		<th class="d-sm-table-cell">{{ total.current_count }}</th>
	</tr>
</tfoot>
</table>


{% endblock %}
