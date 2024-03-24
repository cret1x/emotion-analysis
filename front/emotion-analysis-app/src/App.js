import React, {useState, useEffect} from "react";
import api from './api';
import CloakLoader from "react-spinners/ClockLoader";


const App = () => {

  const downloadFile = (url) => {
    api.get("/getLastReport/", {
      responseType: 'blob',
    }).then(response => {
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'emotional_report.pdf');
      document.body.appendChild(link);
      link.click();
    });
  };

  const [loading, setLoading] = useState(false);

  const [color, setColor] = useState("#0000ff");

  const [reports, setReports] = useState([]);

  const [formData, setFormData] = useState({
    region: '',
    endpoint_url: '',
    aws_access_key_id: '',
    aws_secret_access_key: '',
    bucket_name: '',
    key_name: '',
  });

  const fetchReports = async () => {
    const response = await api.get('/getReportResults/');
    setReports(response.data);
  }

  useEffect(() => {
    fetchReports();
  }, []);

  const handleInputChange = (event) => {
    const value = event.target.value;
    setFormData({...formData, [event.target.name]: value});
  };

  const handleFormSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    await api.post('/requestReport/', formData);
    setLoading(false);
    setFormData({
      region: '',
      endpoint_url: '',
      aws_access_key_id: '',
      aws_secret_access_key: '',
      bucket_name: '',
      key_name: '',
    });
    fetchReports();
  };

  return (
    <div>
      <nav className='navbar navbar-dark bg-primary'>
        <div className='container-fluid'>
          <a className='navbar-brand' href='#'>
            Emotion analysis app
          </a>
        </div>
      </nav>
      <div className="container">
        <form onSubmit={handleFormSubmit}>

          <div className='mb-3 mt-3'>
            <label htmlFor='region' className="form-label">
              Region
            </label>
            <input type='text' className='form-control' id='region' name='region' onChange={handleInputChange} value={formData.region}/>
          </div>

          <div className='mb-3'>
            <label htmlFor='endpoint_url' className="form-label">
              Endpoint url
            </label>
            <input type='text' className='form-control' id='endpoint_url' name='endpoint_url' onChange={handleInputChange} value={formData.endpoint_url}/>
          </div>

          <div className='mb-3'>
            <label htmlFor='aws_access_key_id' className="form-label">
              AWS access key Id
            </label>
            <input type='text' className='form-control' id='aws_access_key_id' name='aws_access_key_id' onChange={handleInputChange} value={formData.aws_access_key_id}/>
          </div>

          <div className='mb-3'>
            <label htmlFor='aws_secret_access_key' className="form-label">
              AWS secret access key
            </label>
            <input type='text' className='form-control' id='aws_secret_access_key' name='aws_secret_access_key' onChange={handleInputChange} value={formData.aws_secret_access_key}/>
          </div>

          <div className='mb-3'>
            <label htmlFor='bucket_name' className="form-label">
              Bucket
            </label>
            <input type='text' className='form-control' id='bucket_name' name='bucket_name' onChange={handleInputChange} value={formData.bucket_name}/>
          </div>

          <div className='mb-3'>
            <label htmlFor='key_name' className="form-label">
              Key
            </label>
            <input type='text' className='form-control' id='key_name' name='key_name' onChange={handleInputChange} value={formData.key_name}/>
          </div>

          <button type='submit' className='btn btn-primary'>
            Analyse emotions
          </button>

          <div className='mb-6 mt-3'>
            <CloakLoader
              color={color}
              loading={loading}
              size={150}
              aria-label="Loading Spinner"
              data-testid="CloakLoader"
            />
          </div>

        </form>
        
        <div className="mb-3 mt-3">
          <button className='btn btn-primary' onClick={() => downloadFile()}>Download last report</button>
        </div>

        <table className='table table-striped table-bordered table-hover'>
          <thead>
            <tr>
              <th>ReportResultId</th>
              <th>Neutral</th>
              <th>Angry</th>
              <th>Disgust</th>
              <th>Fear</th>
              <th>Happy</th>
              <th>Sad</th>
              <th>Surprise</th>
              <th>Looked away</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report) => (
              <tr key={report.id}>
                <td>{report.reportResultId}</td>
                <td>{report.neutral}</td>
                <td>{report.angry}</td>
                <td>{report.disgust}</td>
                <td>{report.fear}</td>
                <td>{report.happy}</td>
                <td>{report.sad}</td>
                <td>{report.surprise}</td>
                <td>{report.lookedAway}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
  
}

export default App;
