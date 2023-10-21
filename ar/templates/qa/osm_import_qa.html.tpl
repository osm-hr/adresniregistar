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
	  <li class="breadcrumb-item" aria-current="page"><a href="index.html">Početna</a></li>
	  <li class="breadcrumb-item" aria-current="page"><a href="qa.html">QA</a></li>
	  <li class="breadcrumb-item" aria-current="page">Kvalitet uvoza</li>
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

            let errorTypeFilter = true;
            if (errorType === 'yes') {
                errorTypeFilter = data[2].indexOf('✅') > -1;
            } else if (errorType === 'street') {
                errorTypeFilter = data[7].indexOf('❌') > -1 || data[7].indexOf('⚠') > -1;
            } else if (errorType === 'street_complete') {
                errorTypeFilter = data[7].indexOf('❌') > -1;
            } else if (errorType === 'street_partial') {
                errorTypeFilter = data[7].indexOf('⚠') > -1;
            } else if (errorType === 'housenumber') {
                errorTypeFilter = data[9].indexOf('❌') > -1 || data[9].indexOf('⚠') > -1;
            } else if (errorType === 'housenumber_complete') {
                errorTypeFilter = data[9].indexOf('❌') > -1;
            } else if (errorType === 'housenumber_partial') {
                errorTypeFilter = data[9].indexOf('⚠') > -1;
            } else if (errorType === 'distance') {
                errorTypeFilter = data[10].indexOf('❌') > -1;
            }

			return errorTypeFilter;
		});

	    var table = $('#list').DataTable({
		    stateSave: true,
		    order: [[0, 'asc']],
		    lengthMenu: [ [10, 100, -1], [10, 50, "All"] ],
		    columnDefs: [
		        { targets: [1], className: 'text-right' },
		    ]
		});

        $('#errorTypeSelect').on('change', function() {
            table.draw();
        });
	} );
    </script>

<h2>Kvalitet uvoza OSM adresa</h2>
<br/>
<p>Ovde možete videti OSM adrese koje imaju tag <code>ref:RS:kucni_broj</code>, ali se nešto ne poklapa sa RGZ-om.
    <br/>
    Može biti da u RGZ-u nema te reference, da je ulica delimično (⚠️) ili potpuno (❌) pogrešna, da je kućni broj delimično (⚠️) ili potpuno (❌) pogrešan ili da je udaljenost između adrese u OSM-u i RGZ-u preko 30 metara.
    <br/>
    Nisu sve stvari isto bitne, pa postoji i kolona prioritet.
    <br/>
    Ukoliko je adresa ili kućni broj <i>delimično</i> pogrešna, to znači da je ima neko veliko ili malo slovo drugačije, ili da je napisana pogrešnim pismom ili da ima neke interpunkcijske znake viška ili manjka.
</p>
<br/>
<br/>

<div class="text-right">
    <label for="errorType">Tip greške:</label>
    <select name="errorType" id="errorTypeSelect">
      <option value="all">Sve</option>
      <option value="street">Adresa</option>
      <option value="street_complete">&nbsp;&nbsp; Potpuno pogrešna</option>
      <option value="street_partial">&nbsp;&nbsp; Delimično pogrešna</option>
      <option value="housenumber">Kućni broj</option>
      <option value="housenumber_complete">&nbsp;&nbsp; Potpuno pogrešan</option>
      <option value="housenumber_partial">&nbsp;&nbsp; Delimično pogrešan</option>
      <option value="distance">Predaleko u odnosu na RGZ-u</option>
    </select>
</div>

<table id="list" class="table table-sm table-striped table-bordered table-hover w-100">
<thead class="thead-dark sticky-top">
	<tr>
        <th>Prioritet</th>
		<th>OSM entitet</th>
		<th>OSM adresa</th>
        <th>OSM kućni broj</th>
        <th>Nađen u RGZ-u</th>
        <th>RGZ opština</th>
        <th>RGZ adresa</th>
        <th>RGZ adresa poklapanje</th>
        <th>RGZ kućni broj</th>
        <th>RGZ kućni broj poklapanje</th>
        <th>Udaljenost [m]</th>
	</tr>
</thead>
<tbody>
	{% for address in addresses %}
	<tr>
        <td>{{ address.priority }}</td>
        <td><a href="{{ address.osm_link }}" target="_blank">{{ address.osm_link_text }}</a></td>
		<td>{{ address.osm_street }}</td>
        <td>{{ address.osm_housenumber }}</td>
        <td>{% if address.found_in_rgz %}✅ (<a href="{{ address.rgz_link }}" target="_blank">loc</a>){% else %}❌{% endif %}</td>
        <td>{% if address.found_in_rgz %}{{ address.rgz_opstina }}{% endif %}</td>
        <td>{% if address.found_in_rgz %}{{ address.rgz_street }}{% endif %}</td>
        <td>
            {% if address.found_in_rgz %}
                {% if address.rgz_street_match == 1 %}✅
                {% elif address.rgz_street_match == 0 %}⚠️
                {% else %}❌
                {% endif %}
            {% endif %}
        </td>
        <td data-order="{% if address.found_in_rgz %}{{ address.rgz_housenumber_order }}{% else %}0{% endif %}">{% if address.found_in_rgz %}{{ address.rgz_housenumber }}{% endif %}</td>
        <td>
            {% if address.found_in_rgz %}
                {% if address.rgz_housenumber_match == 1 %}✅
                {% elif address.rgz_housenumber_match == 0 %}⚠️
                {% else %}❌
                {% endif %}
            {% endif %}
        </td>
        <td data-order="{% if address.found_in_rgz %}{{ '{0:0.0f}'.format(address.distance) }}{% else %}0{% endif %}">
            {% if address.found_in_rgz %}
                {% if address.distance <= 30 %}✅{% else %}❌{% endif %} &nbsp; {{ '{0:0.0f}'.format(address.distance) }}
            {% endif %}
        </td>
	</tr>
	{% endfor %}
</tbody>
</table>

{% endblock %}

