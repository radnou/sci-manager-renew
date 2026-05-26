-- 042: Atomic increment for quittance counter
-- Add atomic RPC function to prevent race conditions on quittance sequential numbers

CREATE OR REPLACE FUNCTION increment_quittance_counter(p_sci_id UUID, p_annee_mois VARCHAR)
RETURNS INTEGER AS $$
DECLARE
    v_nouveau INTEGER;
BEGIN
    INSERT INTO quittance_compteur (sci_id, annee_mois, dernier_numero)
    VALUES (p_sci_id, p_annee_mois, 1)
    ON CONFLICT (sci_id, annee_mois)
    DO UPDATE SET dernier_numero = quittance_compteur.dernier_numero + 1
    RETURNING dernier_numero INTO v_nouveau;
    
    RETURN v_nouveau;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
