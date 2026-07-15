export default function ResultsTable({ results }) {

    return (

        <div className="bg-slate-900 p-5 rounded-xl mt-8">

            <h2 className="text-xl font-bold mb-4">
                Results
            </h2>

            <table className="w-full">

                <thead>

                    <tr className="text-left border-b border-slate-700">

                        <th>ID</th>
                        <th>Distance</th>
                        <th>Metadata</th>

                    </tr>

                </thead>

                <tbody>

                    {results.map((r,index)=>(

                        <tr key={index} className="border-b border-slate-800">

                            <td>{r.item.id}</td>

                            <td>{r.distance.toFixed(4)}</td>

                            <td>{JSON.stringify(r.item.metadata)}</td>

                        </tr>

                    ))}

                </tbody>

            </table>

        </div>

    );

}