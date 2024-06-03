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
                <li><b>Datum brisanja</b> &mdash; Datum prvog primećivanja da adresa nije više u RGZ-u</li>
                <li><b>„removed:ref:RS:kucni_broj” tag</b> &mdash; „removed:ref:RS:kucni_broj” oznaka na adresi, vrednost koju je adresa nekad imala u RGZ-u</li>
                <li><b>„ref:RS:kucni_broj” tag</b> &mdash; „ref:RS:kucni_broj” oznaka na adresi, ukoliko trenutno postoji. Ako postoje obe vrednosti, treba obrisati „removed:ref:RS:kucni_broj” oznaku</li>
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
    <li class="breadcrumb-item" aria-current="page"><a href="../../index.html">DINA</a></li>
	<li class="breadcrumb-item" aria-current="page"><a href="../index.html">Adrese</a></li>
	<li class="breadcrumb-item" aria-current="page"><a href="../qa.html">QA</a></li>
    <li class="breadcrumb-item" aria-current="page"><a href="../removed_addresses.html">Obrisane RGZ adrese</a></li>
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
		    stateDuration: 0,
		    order: [[1, 'desc']],
		    lengthMenu: [ [10, 50, -1], [10, 50, "All"] ],
		    columnDefs: [
		        { targets: [2], className: 'text-right' },
		        { targets: [4], className: 'text-right' },
		    ]
		});
	} );
    </script>

<h2>Obrisane RGZ adrese za opštinu „{{ opstina_name }}”</h2>
<br/>
<p>Ovde možete videti sve RGZ adrese koje smo uneli u OSM, ali su one od tad izbrisane iz RGZ-a.
    Adresa brisanja je najranije vreme kada smo primetili da adresa više nije u RGZ-u. Ukoliko imate lokalno znanje,
    slobodno obrišite ove adrese (ili cele zgrade ukoliko više ne postoji).
    Ukoliko postoji „removed:ref:RS:kucni_broj” oznake, sigurno treba obrisati „removed:ref:RS:kucni_broj” oznaku!
    U suprotnom, dogovor zajednice je da ih ostavimo neke vreme (npr. 2 godine) jer neko može da ih koristi za navođenje ili su možda još u upotrebi.
    U gornjem desnom uglu je filtriranje. Klikom na <a href="" data-toggle="modal" data-target="#exampleModal">„Pomoć”</a> u gornjem meniju dobićete više informacija o kolonama u ovoj tabeli.
    </p>
<br/>
<br/>


<table id="list" class="table table-sm table-striped table-bordered table-hover w-75">
<thead class="thead-dark sticky-top">
	<tr>
		<th>OSM id</th>
        <th>Ulica</th>
        <th>Broj</th>
        <th>Datum brisanja</th>
        <th>„removed:ref:RS:kucni_broj” tag</th>
        <th>„ref:RS:kucni_broj” tag</th>
	</tr>
</thead>
<tbody>
	{% for address in addresses %}
	<tr>
		<td><a href="{{ address.osm_link }}" target="_blank">{{ address.osm_id }}</a></td>
        <td>{{ address.street}}</td>
        <td>{{ address.housenumber}}</td>
        <td>{{ address.removal_date}}</td>
        <td>{{ address.removed_rgz_id}}</td>
        <td>{{ address.current_rgz_id}}</td>
	</tr>
	{% endfor %}
</tbody>
</table>

{% endblock %}

