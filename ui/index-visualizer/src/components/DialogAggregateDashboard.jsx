import { Grid, Card, CardContent, Typography } from '@mui/material';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { summariseDialogs } from '../utils/stats';

const colors = ['#8884d8','#82ca9d','#ffc658','#ff7f50','#8dd1e1','#a4de6c','#d0ed57','#8884d8'];

export default function DialogAggregateDashboard({ rows }) {
  const stats = summariseDialogs(rows);

  const characterData = Object.entries(stats.byCharacter).sort((a,b)=>b[1]-a[1]).slice(0,10)
                               .map(([k,v]) => ({ name: k, value: v }));
  const emotionData = Object.entries(stats.byEmotion).map(([k,v]) => ({ name: k, value: v }));

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
      <Grid item xs={12} sm={3}><KPI label="Scenes" val={stats.totalScenes} /></Grid>
      <Grid item xs={12} sm={3}><KPI label="Total dialogues" val={stats.totalDialogues} /></Grid>
      <Grid item xs={12} sm={3}><KPI label="Avg dialogues/scene" val={stats.avgDialoguesPerScene} /></Grid>
      <Grid item xs={12} sm={3}><KPI label="Chapters with dialogue" val={stats.chaptersWithDialogue} /></Grid>

      <Grid item xs={12} md={6} height={320}>
        <Typography variant="subtitle1" align="center">Character dialogue frequency</Typography>
        <ResponsiveContainer>
          <BarChart data={characterData} layout="vertical" margin={{ left: 60 }}>
            <XAxis type="number" hide />
            <YAxis type="category" dataKey="name" width={120} />
            <Tooltip />
            <Bar dataKey="value" >
              {characterData.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Grid>

      <Grid item xs={12} md={6} height={320}>
        <Typography variant="subtitle1" align="center">Emotional tone distribution</Typography>
        <ResponsiveContainer>
          <PieChart>
            <Pie data={emotionData} dataKey="value" nameKey="name" label>
              {emotionData.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </Grid>
    </Grid>
  );
}