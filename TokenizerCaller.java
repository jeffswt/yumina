
import java.io.PrintStream;
import java.io.IOException;
import java.util.Scanner;
import java.util.List;

import org.atilika.kuromoji.Token;
import org.atilika.kuromoji.Tokenizer;
import org.atilika.kuromoji.Tokenizer.Mode;

public class TokenizerCaller
{
	public static void main(String[] args) throws IOException
    {
		Tokenizer tokenizer = Tokenizer.builder().build();
		Scanner ioScanner = new Scanner(System.in, "UTF-8");
        PrintStream outStream = new PrintStream(System.out, true, "UTF-8");
		String line;
		while (true) {
            try {
                line = ioScanner.nextLine();
            } catch (Exception err) {
                break;
            }
            if (line.equals("__FORCE_EXIT__")) {
                break;
            }
    		List<Token> result = tokenizer.tokenize(line);
			for (Token token : result) {
                String[] array = token.getAllFeaturesArray();
                String out;
                if (array.length > 7) {
                    out = token.getSurfaceForm()
                        + "__SPLIT__"
                        + token.getAllFeaturesArray()[7];
                } else {
                    out = token.getSurfaceForm()
                        + "__SPLIT__";
                }
                outStream.println(out);
			}
            outStream.println("__ANALYSIS_COMPLETE__");
            System.out.flush();
		}
		return ;
	}
}
