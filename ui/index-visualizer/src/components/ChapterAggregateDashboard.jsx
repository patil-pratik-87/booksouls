import { Grid, Card, CardContent, Typography } from '@mui/material';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { summariseChapters } from '../utils/stats';

const colors = ['#8884d8','#82ca9d','#ffc658','#ff7f50','#8dd1e1','#a4de6c','#d0ed57','#8884d8'];

export default function ChapterAggregateDashboard({ rows }) {
  const stats = summariseChapters(rows);

  const themeData = Object.entries(stats.byTheme).map(([k,v]) => ({ name: k, value: v }));
  const entityData = Object.entries(stats.byEntity).sort((a,b)=>b[1]-a[1]).slice(0,10)
                             .map(([k,v]) => ({ name: k, value: v }));

  const KPI = ({ label, val }) => (
    <Card sx={{ textAlign:'center' }}>
      <CardContent>
        <Typography variant="subtitle2">{label}</Typography>
        <Typography variant="h4">{val.toLocaleString()}</Typography>
      </CardContent>
    </Card>
  );

  return (
    <Grid container spacing={2} sx={{ p: 2 }}>
      <Grid item xs={12} sm={3}><KPI label="Chapters" val={stats.total} /></Grid>
      <Grid item xs={12} sm={3}><KPI label="Total sections" val={stats.sections} /></Grid>
      <Grid item xs={12} sm={3}><KPI label="Total tokens" val={stats.tokens} /></Grid>
      <Grid item xs={12} sm={3}><KPI label="Total words" val={stats.words} /></Grid>

      <Grid item xs={12} sm={6}><KPI label="Avg tokens/chapter" val={stats.avgTokensPerChapter} /></Grid>
      <Grid item xs={12} sm={6}><KPI label="Avg words/chapter" val={stats.avgWordsPerChapter} /></Grid>

      <Grid item xs={12} md={6} height={320}>
        <Typography variant="subtitle1" align="center">Theme distribution</Typography>
        <ResponsiveContainer>
          <PieChart>
            <Pie data={themeData} dataKey="value" nameKey="name" label>
              {themeData.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </Grid>

      <Grid item xs={12} md={6} height={320}>
        <Typography variant="subtitle1" align="center">Top 10 entities</Typography>
        <ResponsiveContainer>
          <BarChart data={entityData} layout="vertical" margin={{ left: 40 }}>
            <XAxis type="number" hide />
            <YAxis type="category" dataKey="name" width={120} />
            <Tooltip />
            <Bar dataKey="value" >
              {entityData.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Grid>
    </Grid>
  );
}