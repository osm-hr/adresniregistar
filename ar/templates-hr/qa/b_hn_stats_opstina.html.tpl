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
                <li><b>Naselje</b> &mdash; Naselje za koju se odnosi izveštaj</li>
                <li><b>Odnos</b> &mdash; Količnik broja zgrada i broja kućnih brojeva</li>
                <li><b>Broj zgrada (OSM)</b> &mdash; Ukupan broj pronađenih zgrada u OSM-u na teritoriji ovog naselja</li>
                <li><b>Broj kućnih brojeva (RGZ)</b> &mdash; Ukupan broj pronađenih kućnih brojeva u RGZ-u na teritoriji ovog naselja</li>
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
    <li class="breadcrumb-item" aria-current="page"><a href="../../index.html">Adrese</a></li>
	<li class="breadcrumb-item" aria-current="page"><a href="../index.html">Adrese</a></li>
	<li class="breadcrumb-item" aria-current="page"><a href="../qa.html">Izveštaji</a></li>
    <li class="breadcrumb-item" aria-current="page"><a href="index.html">Odnos zgrada i kućnih brojeva</a></li>
    <li class="breadcrumb-item" aria-current="page">{{ opstina }}</li>
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
		    order: [[0, 'asc'], [1, 'asc']],
		    lengthMenu: [ [10, 50, -1], [10, 50, "All"] ],
		    columnDefs: [
		        { targets: [2], className: 'text-right' },
		        { targets: [3], className: 'text-right' }
		    ]
		});
	} );
    </script>

<h2>Broj zgrada i kućnih brojeva za opštinu „{{ opstina }}”</h2>
<br/>
<p>Ovde možete videti broj zgrada iz OSM-a, kao i broj kućnih brojeva iz RGZ-a, kao i njihov odnos u opštini „{{ opstina }}”.
    Ovo može da pomogne da se vidi gde najviše fale zgrade u OSM-u jer zgrade i kućni brojevi treba da su korelisani.
    U gornjem desnom uglu je filtriranje. Klikom na <a href="" data-toggle="modal" data-target="#exampleModal">„Pomoć”</a> u gornjem meniju dobićete više informacija o kolonama u ovoj tabeli.
    </p>
<br/>
<br/>

<table id="list" class="table table-sm table-striped table-bordered table-hover w-50">
<thead class="thead-dark sticky-top">
	<tr>
		<th>Naselje</th>
        <th>Odnos</th>
        <th>Broj zgrada (OSM)</th>
        <th>Broj kućnih brojeva (RGZ)</th>
	</tr>
</thead>
<tbody>
	{% for naselje in naselja %}
	<tr>
		<td>{{ naselje.naselje }}</td>
        <td data-order="{{ naselje.ratio_order }}">{{ naselje.ratio }}</td>
        <td>{{ naselje.building_count }}</td>
        <td>{{ naselje.addresses_count }}</td>
	</tr>
	{% endfor %}
</tbody>
</table>

{% endblock %}
