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
			<li><b>RGZ opština</b> &mdash; Opština iz RGZ-a</li>
			<li><b>OSM adresa i kućni broj</b> &mdash; Adresa i kućni broj iz OSM-a, data kao link ka OSM entitetu</li>
			<li><b>RGZ lokacija</b> &mdash; Link ka lokaciji iz RGZ-a, da može da se uporedi sa OSM lokacijom</li>
			<li><b>Udaljenost [m]</b> &mdash; Udaljenost između OSM entiteta i RGZ lokacije, data u metrima</li>
			<li><b>Beleška</b> &mdash; Ukoliko postoji „note” tag kod OSM entiteta koji sadrži reč „RGZ”, ona će biti prikazana ovde</li>
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
	<li class="breadcrumb-item" aria-current="page">Kvalitet uvoza - prevelike udaljenosti</li>
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
		$.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
			let errorType = $("#errorTypeSelect option:selected").val();
			let noteType = $("#noteTypeSelect option:selected").val();

            let errorTypeFilter = true;
            if (errorType === 'gt50') {
                errorTypeFilter = data[3] > 50;
            } else if (errorType === 'gt100') {
                errorTypeFilter = data[3] > 100;
            } else if (errorType === 'gt1000') {
                errorTypeFilter = data[3] > 1000;
            }

            let noteTypeFilter = true;
            if (noteType === 'yes') {
                noteTypeFilter = data[4] != '';
            } else if (noteType === 'no') {
                noteTypeFilter = data[4] === '';
            }

			return errorTypeFilter && noteTypeFilter;
		});

	    var table = $('#list').DataTable({
		    stateSave: true,
		    order: [[0, 'asc']],
		    lengthMenu: [ [10, 100, -1], [10, 50, "All"] ]
		});

        $('#errorTypeSelect').on('change', function() {
            table.draw();
        });
        $('#noteTypeSelect').on('change', function() {
            table.draw();
        });

        $(function () {
            $('[data-toggle="tooltip"]').tooltip()
        });
	} );
    </script>

<h2>Kvalitet uvoza - prevelike udaljenosti</h2>
<br/>
<p>Ovde možete videti OSM adrese koje imaju tag <code>ref:RS:kucni_broj</code>, ali je udaljenost u odnosu na RGZ prevelika.
    <br/>
    Udaljenosti mogu da se filtriraju po par vrednosti - preko 30m, 50m, 100m i 1000m.
</p>

<div class="text-right">
    <label for="errorType">Greška udaljenosti:</label>
    <select name="errorType" id="errorTypeSelect">
      <option value="all">Sve (preko 30m)</option>
      <option value="gt50">Preko 50m</option>
      <option value="gt100">Preko 100m</option>
      <option value="gt1000">Preko 1000m</option>
    </select>
    <br/>
    <label for="errorType">Ima belešku:</label>
    <select name="noteType" id="noteTypeSelect">
      <option value="all"></option>
      <option value="yes">Da</option>
      <option value="no">Ne</option>
    </select>
</div>

<table id="list" class="table table-sm table-striped table-bordered table-hover w-100">
<thead class="thead-dark sticky-top">
	<tr>
		<th>RGZ opština</th>
		<th>OSM adresa i kućni broj</th>
		<th>RGZ lokacija</th>
        <th>Udaljenost [m]</th>
        <th>Beleška</th>
	</tr>
</thead>
<tbody>
	{% for address in addresses %}
	<tr>
        <td>{{ address.rgz_opstina }}</td>
		<td><a href="{{ address.osm_link }}" target="_blank">{{ address.osm_street }} {{ address.osm_housenumber }}</a></td>
		<td><a href="{{ address.rgz_link }}" target="_blank">{{ address.location_lat }}, {{ address.location_lon }}</a></td>
        <td data-order="{{ '{0:0.0f}'.format(address.distance) }}">
            {{ '{0:0.0f}'.format(address.distance) }}
        </td>
        <td>{% if address.note %}<a href="#" class="text-dark" style="text-decoration: underline;text-decoration-style: dotted;" data-toggle="tooltip" title="{{ address.note }}">{{ address.note_short }} ↗</a>{% endif %}
        </td>
	</tr>
	{% endfor %}
</tbody>
</table>

{% endblock %}

