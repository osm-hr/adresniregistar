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
                <li><b>OSM id</b> &mdash; ID adrese iz OSM-a, dat kao link</li>
                <li><b>Ulica</b> &mdash; Ulica iz adrese (addr:street oznaka)</li>
                <li><b>Kućni broj</b> &mdash; Kućni broj iz adrese (addr:housenumber oznaka)</li>
                <li><b>„name” tag</b> &mdash; „name” oznaka na adresi, ukoliko postoji</li>
                <li><b>„amenity” tag</b> &mdash; „amenity” oznaka na adresi, ukoliko postoji</li>
                <li><b>„shop” tag</b> &mdash; „shop” oznaka na adresi, ukoliko postoji</li>
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
      <li class="breadcrumb-item" aria-current="page"><a href="../unaccounted_osm_addresses.html">OSM adrese bez ref:RS:kucni_broj</a></li>
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
		        { targets: [2], className: 'text-right' },
		        //{ targets: '_all', visible: false }
		    ]
		});
		$('#list_resolution').DataTable({
		    stateSave: true,
		    order: [[1, 'desc']]
		});
	} );
    </script>

<h2>OSM adrese bez ref:RS:kucni_broj oznake za opštinu „{{ opstina_name }}”</h2>
<br/>
<p>Ovde možete videti sve adrese u OpenStreetMap-ama koje nemaju ref:RS:kucni_broj oznaku.
    Ovo znači ili da nisu spojene sa RGZ podacima, ili da je teško spojiti ih sa RGZ podacima (postoje na terenu, treba izaći na teren i proveriti...).
    U gornjem desnom uglu je filtriranje. Klikom na "Pomoć" u gornjem meniju dobićete više informacija o kolonama u ovoj tabeli.
    </p>
<br/>
<br/>


<table id="list" class="table table-sm table-striped table-bordered table-hover w-50">
<thead class="thead-dark sticky-top">
	<tr>
		<th>OSM id</th>
        <th>Ulica</th>
        <th>Broj</th>
        <th>„name” tag</th>
        <th>„amenity” tag</th>
        <th>„shop” tag</th>
	</tr>
</thead>
<tbody>
	{% for address in addresses %}
	<tr>
		<td><a href="{{ address.osm_link }}" target="_blank">{{ address.osm_id }}</a></td>
        <td>{{ address.street}}</td>
        <td>{{ address.housenumber}}</td>
        <td>{{ address.name}}</td>
        <td>{{ address.amenity}}</td>
        <td>{{ address.shop}}</td>
	</tr>
	{% endfor %}
</tbody>
</table>

{% endblock %}

